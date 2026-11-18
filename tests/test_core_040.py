"""Features of TextForge 0.3.x/0.4.0 exposed through the portable API.

Error details, ``tryi``, section and file instructions, joined pipelines,
built-in variables, execution profiles and pipeline names.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import pytest
from textforge import (
    ErrorParameter,
    ExecutionProfile,
    Instruction,
    Pipeline,
    Processor,
    TextForgeError,
    TraceFrame,
    __version__,
    get_var,
)


def failure(plan: Pipeline, text: str) -> TextForgeError:
    with pytest.raises(TextForgeError) as raised:
        plan.compile()(text)
    return raised.value


def test_errors_carry_kind_trace_parameters_hint_and_report() -> None:
    error = failure(Pipeline().delete_single(9), "abc")
    assert (error.code, error.kind, error.stage) == (12, "IndexOutOfRange", "execution")
    assert error.trace == (TraceFrame("dls 9;"),)
    assert error.parameters == (ErrorParameter("index", "9"),)
    assert error.ignorable is True
    assert error.cause is None
    assert error.hint is not None and "from 0" in error.hint
    assert error.report.startswith("error[12] IndexOutOfRange: ")
    assert "\x1b[" not in error.report
    assert "Parameters:" in error.report


def test_error_parameters_record_how_a_value_was_written() -> None:
    error = failure(Pipeline().var("n", 9).delete_single(get_var("n")), "abc")
    (parameter,) = error.parameters
    assert parameter.name == "index"
    assert parameter.value == "9"
    assert parameter.written is not None


def test_nested_errors_trace_the_container_first() -> None:
    error = failure(Pipeline().iter(2, Pipeline().delete_single(9)), "abc")
    assert len(error.trace) == 2
    assert error.trace[0].instruction.startswith("iter")
    assert error.trace[0].note is not None
    assert error.trace[-1].instruction == "dls 9;"


def test_io_errors_keep_their_cause_apart(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    error = failure(Pipeline().append_file(str(missing)), "x")
    assert error.kind == "FileOpeningError"
    assert error.cause is not None
    assert str(missing) in error.message


def test_detailed_errors_survive_pickling() -> None:
    error = failure(Pipeline().delete_single(9), "abc")
    restored = pickle.loads(pickle.dumps(error))
    for field in ("kind", "trace", "parameters", "cause", "hint", "ignorable", "report"):
        assert getattr(restored, field) == getattr(error, field)
    frame = TraceFrame("dls 9;", "p.textforge:3", None)
    assert pickle.loads(pickle.dumps(frame)) == frame
    assert repr(frame) == "TraceFrame(instruction='dls 9;', location='p.textforge:3', note=None)"


def test_try_ignore_skips_failures_and_restores_variables() -> None:
    plan = (
        Pipeline()
        .var("n", "a")
        .block_assoc("change", lambda b: b.mut_var("n", "b").add_to_end("?").delete_single(99))
        .try_ignore(Instruction("cblk", "change"))
        .add_to_end("{{n}}")
    )
    assert plan.compile()("xyz") == "xyza"
    assert Pipeline().try_ignore(Pipeline().to_reverse()).compile()("abc") == "cba"
    generic = Pipeline(Instruction("tryi", Instruction("dls", 99))).compile()
    assert generic("abc") == "abc"


def test_try_ignore_never_ignores_safety_limits() -> None:
    processor = Processor()
    profile = ExecutionProfile.balanced().with_limits(max_generated_bytes=4, max_iterations=None)
    processor.set_profile(profile)
    id = processor.register(Pipeline().try_ignore(Pipeline().repeat(9)))
    with pytest.raises(TextForgeError) as raised:
        processor.process_all(id, "ab")
    assert (raised.value.code, raised.value.kind) == (31, "LimitExceededError")
    assert raised.value.ignorable is False


def test_section_instructions_scope_their_inner_instruction() -> None:
    assert Pipeline().on_line(0, Pipeline().to_reverse()).compile()("ab\ncd") == "ba\ncd"
    assert Pipeline().on_chunk(0, 1, Instruction("tua")).compile()("abc") == "ABc"
    lines = Pipeline().on_line_interval(1, 99, Pipeline().join_lines("+"))
    assert lines.compile()("a\nb\nc") == "a\nb+c"


@pytest.mark.parametrize("extension", ["textforge", "textforgebc"])
def test_new_instructions_round_trip_through_files(tmp_path: Path, extension: str) -> None:
    processor = Processor()
    plan = (
        Pipeline()
        .try_ignore(Pipeline().delete_single(99))
        .on_line(0, Pipeline().to_uppercase_all())
        .on_chunk(0, 0, Pipeline().add_to_end("!"))
        .on_line_interval(0, 0, Pipeline().to_reverse())
    )
    id = processor.register(plan)
    path = tmp_path / f"plan.{extension}"
    if extension == "textforge":
        processor.write_pipeline_to_file(id, path)
        restored = processor.get_pipeline_from_file(path)
    else:
        processor.write_to_bytecode_file(id, path)
        restored = processor.read_from_bytecode_file(path)
    assert processor.process_all(restored, "ab\ncd") == processor.process_all(id, "ab\ncd")
    assert processor.get_text_transform_vec(id) == [
        "tryi dls 99;\n",
        "onln 0 apply tua;\n",
        "onck 0 0 apply ate !;\n",
        "onlni 0 0 apply rev;\n",
    ]


def test_file_instructions(tmp_path: Path) -> None:
    part = tmp_path / "part.txt"
    part.write_text("<p>", encoding="utf-8")
    written = tmp_path / "written.txt"
    plan = (
        Pipeline()
        .write_to_file(str(written))
        .append_file(str(part))
        .prepend_file(str(part))
        .insert_file(1, str(part))
    )
    assert plan.compile()("ab") == "<p<p>>ab<p>"
    assert written.read_text(encoding="utf-8") == "ab"
    generic = Pipeline(Instruction("inf", 0, str(part))).compile()
    assert generic("x") == "<p>x"


def test_pipeline_join_runs_another_file(tmp_path: Path) -> None:
    joined = tmp_path / "upper.textforge"
    joined.write_text("tua;\nate '!';\n", encoding="utf-8")
    plan = Pipeline().add_to_beginning(">").pipeline_join(str(joined)).add_to_end("<")
    assert plan.compile()("ab") == ">AB!<"
    processor = Processor()
    id = processor.register(plan)
    bytecode = tmp_path / "outer.tfb"
    processor.write_to_bytecode_file(id, bytecode)
    joined.unlink()  # bytecode embeds joined pipelines
    restored = processor.read_from_bytecode_file(bytecode)
    assert processor.process_all(restored, "ab") == ">AB!<"


def test_pipeline_join_errors_are_reported_when_registering(tmp_path: Path) -> None:
    with pytest.raises(TextForgeError) as raised:
        Processor().register(Pipeline().pipeline_join(str(tmp_path / "missing.textforge")))
    assert raised.value.stage == "persistence"


def test_builtin_variables() -> None:
    plan = Pipeline().add_to_end(" {{__LEN_CHARS__}} {{__LINES__}} {{__TEXTFORGE_VERSION__}}")
    assert plan.compile()("é\n🍌") == "é\n🍌 3 2 0.4.0"
    error = failure(Pipeline().var("__LINES__", 1), "")
    assert error.stage in {"validation", "execution"}


def test_pipeline_names() -> None:
    processor = Processor()
    id = processor.register(Pipeline().add_to_end("{{__PIPELINE_NAME__}}"))
    assert processor.pipeline_name(id) == id
    processor.set_pipeline_name(id, "report")
    assert processor.pipeline_name(id) == "report"
    assert processor.process_all(id, "name: ") == "name: report"
    with pytest.raises(TextForgeError):
        processor.pipeline_name("missing")


def test_execution_profiles() -> None:
    processor = Processor()
    assert processor.profile() == ExecutionProfile.balanced()
    assert ExecutionProfile.balanced().spool_threshold == 1024 * 1024
    assert ExecutionProfile.low_memory() == ExecutionProfile.preset("low-memory")
    assert ExecutionProfile.fast().spool_threshold == 256 * 1024 * 1024
    unlimited = ExecutionProfile.fast().unlimited()
    processor.set_profile(unlimited)
    assert processor.profile() == unlimited
    with pytest.raises(ValueError, match="balanced, low-memory and fast"):
        ExecutionProfile.preset("tiny")
    with pytest.raises(TypeError):
        ExecutionProfile(True)
    with pytest.raises(OverflowError):
        ExecutionProfile(1, max_iterations=-1)
    with pytest.raises(TypeError):
        processor.set_profile("fast")  # type: ignore[arg-type]


def test_iteration_limit() -> None:
    processor = Processor()
    processor.set_profile(
        ExecutionProfile.balanced().with_limits(max_generated_bytes=None, max_iterations=2)
    )
    id = processor.register(Pipeline().iter(3, Pipeline().add_to_end("!")))
    with pytest.raises(TextForgeError) as raised:
        processor.process_all(id, "")
    assert raised.value.kind == "LimitExceededError"


def test_version_is_a_string() -> None:
    assert isinstance(__version__, str)
