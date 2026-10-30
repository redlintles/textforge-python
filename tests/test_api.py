"""Exercise the installed extension at its Python/portable boundary."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from textforge import Instruction, Pipeline, Processor, TextForgeError, Variable


@pytest.mark.parametrize("text", ["", "é", "🍌", "e\u0301", "a\x00b"])
def test_unicode_and_reuse(text: str) -> None:
    source = Pipeline().add("atb", "🍌")
    compiled = source.compile()
    assert compiled(text) == "🍌" + text
    assert compiled.process(text) == "🍌" + text
    assert source.compile()(text) == compiled(text)


def test_identity_and_immutable_edits() -> None:
    base = Pipeline()
    changed = base.add("ate", "!")
    assert base.compile()("x") == "x"
    assert changed.compile()("x") == "x!"
    assert Pipeline(Instruction("tbs")).compile()(" x ") == "x"


def test_variables_interpolation_and_nested_instruction() -> None:
    plan = (
        Pipeline()
        .add("val", "n", "2")
        .add("rpt", Variable("n"))
        .add("ate", "[[ 2 + 3 ]]")
        .add("rpt", 2)
    )
    assert plan.compile()("x") == "xx5xx5"
    nested = Pipeline().add("iter", 2, Instruction("atb", "🍌"))
    assert nested.compile()("é") == "🍌🍌é"


def test_block_body_reuse_and_conditional_semantics() -> None:
    body = Pipeline().add("ate", "!")
    plan = Pipeline().block("dynamic 🍌", body).call_block("dynamic 🍌")
    assert plan.compile()("x") == "x!"
    assert plan.compile()("y") == "y!"
    assert body.compile()("z") == "z!"
    conditional = Pipeline().contains_each(
        "x", Pipeline().add("rmp", "x").add("ate", "should not run")
    )
    assert conditional.compile()("x") == ""
    assert conditional.compile()("é") == "é"


def test_conversion_validation_and_execution_errors() -> None:
    with pytest.raises(TextForgeError) as raised:
        Pipeline().add("unknown").compile()
    assert raised.value.stage == "conversion"
    assert raised.value.code == 2
    assert raised.value.instruction == "unknown"
    assert raised.value.message
    assert "\x1b" not in str(raised.value)
    with pytest.raises(TextForgeError) as raised:
        Pipeline().add("atb").compile()
    assert raised.value.stage == "validation"
    with pytest.raises(TextForgeError) as raised:
        Pipeline().add("rpt", Variable("missing")).compile()("x")
    assert raised.value.stage == "execution"


def test_python_argument_validation() -> None:
    with pytest.raises(TypeError):
        Instruction("rpt", True)
    with pytest.raises(OverflowError):
        Instruction("rpt", -1)
    with pytest.raises(OverflowError):
        Instruction("rpt", 2**64)
    invalid: tuple[object, ...] = (None, 1.5, [], b"x")
    for value in invalid:
        with pytest.raises(TypeError):
            Instruction("atb", value)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Pipeline("tbs")  # type: ignore[arg-type]


def test_depth_is_bounded() -> None:
    instruction = Instruction("tbs")
    for _ in range(32):
        instruction = Instruction("iter", 1, instruction)
    with pytest.raises(TypeError):
        Instruction("iter", 1, instruction)
    plan = Pipeline()
    for _ in range(32):
        plan = Pipeline().contains_each("x", plan)
    with pytest.raises(ValueError):
        Pipeline().contains_each("x", plan)


def test_readonly_descriptions() -> None:
    instruction = Instruction("iter", 2, Instruction("ate", "!"))
    assert instruction.name == "iter"
    assert instruction.arguments[0] == 2
    child = instruction.arguments[1]
    assert isinstance(child, Instruction)
    assert child.arguments == ("!",)
    reference = Variable("n")
    assert reference.name == "n"
    with pytest.raises(AttributeError):
        reference.name = "other"  # type: ignore[misc]


def test_registry_atomicity_snapshots_and_context_reset() -> None:
    processor = Processor()
    id = processor.register(Pipeline().add("atb", "🍌"))
    assert processor.transform_exists(id)
    assert processor.list_transforms() == [id]
    assert processor.process_all(id, "x") == "🍌x"
    assert processor.run_transform(id, "é") == "🍌é"
    assert processor.get_transform_vec(id)[0].arguments == ("🍌",)
    assert "atb" in processor.get_text_transform_vec(id)[0]
    with pytest.raises(TextForgeError):
        processor.register(Pipeline().add("atb"))
    assert processor.list_transforms() == [id]
    cloned = processor.clone_pipeline(id)
    processor.remove_transform(id)
    assert not processor.transform_exists(id)
    assert processor.process_all(cloned, "x") == "🍌x"
    with pytest.raises(TextForgeError):
        processor.process_all(id, "x")
    processor.process_single(Instruction("val", "n", "2"), "x")
    with pytest.raises(TextForgeError):
        processor.process_single(Instruction("rpt", Variable("n")), "x")


def test_files_and_bytecode_roundtrip(tmp_path: Path) -> None:
    processor = Processor()
    id = processor.register(Pipeline().add("tbs").add("ate", "🍌"))
    text = tmp_path / "pipeline é.textforge"
    bytecode = tmp_path / "pipeline 🍌.textforgebc"
    # Text export in the current core requires an existing destination.
    text.touch()
    bytecode.touch()
    processor.write_pipeline_to_file(id, text)
    processor.write_to_bytecode_file(id, bytecode)
    text_id = processor.get_pipeline_from_file(str(text))
    bytecode_id = processor.read_from_bytecode_file(bytecode)
    assert processor.process_all(text_id, " é ") == "é🍌"
    assert processor.process_all(bytecode_id, " é ") == "é🍌"
    input = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    input.write_text(" é ", encoding="utf-8")
    processor.process_file(id, input, output)
    assert output.read_text(encoding="utf-8") == "é🍌"
    with pytest.raises(TextForgeError) as raised:
        processor.get_pipeline_from_file(tmp_path / "missing.textforge")
    assert raised.value.stage == "persistence"
    assert processor.list_transforms() == sorted([id, text_id, bytecode_id])


def test_batch_preserves_order_and_errors(tmp_path: Path) -> None:
    processor = Processor()
    id = processor.register(Pipeline().add("ate", "!"))
    input = tmp_path / "input.txt"
    input.write_text("é", encoding="utf-8")
    outputs = [tmp_path / f"out{i}.txt" for i in range(3)]
    results = processor.process_batch(
        [(input, id, outputs[0]), (input, "missing", outputs[1]), (input, id, outputs[2])],
        threads=2,
    )
    assert results[0] is None
    assert isinstance(results[1], TextForgeError)
    assert results[1].stage == "execution"
    assert results[2] is None
    assert outputs[0].read_text(encoding="utf-8") == "é!"
    assert outputs[2].read_text(encoding="utf-8") == "é!"
    assert processor.process_batch([]) == []


def test_single_and_debug_execution() -> None:
    processor = Processor()
    instruction = Instruction("atb", "🍌")
    assert processor.process_single(instruction, "é") == "🍌é"
    assert processor.process_single_with_debug(instruction, "é") == "🍌é"
    id = processor.register(Pipeline(instruction))
    assert processor.process_all_with_debug(id, "é") == "🍌é"


def test_compiled_shared_across_threads() -> None:
    pipeline = Pipeline().add("ate", "!").compile()
    texts = ["", "é", "🍌", "e\u0301"] * 20
    with ThreadPoolExecutor(max_workers=4) as executor:
        assert list(executor.map(pipeline.process, texts)) == [text + "!" for text in texts]


def test_documented_examples() -> None:
    import doctest

    import textforge

    result = doctest.testmod(textforge, raise_on_error=True)
    assert result.attempted >= 6


def test_snapshot_can_be_used_as_nested_instruction() -> None:
    processor = Processor()
    id = processor.register(Pipeline().add("ate", "!"))
    instruction = processor.get_transform_vec(id)[0]
    assert Pipeline().add("iter", 2, instruction).compile()("é") == "é!!"


def test_exception_can_be_pickled() -> None:
    import pickle

    with pytest.raises(TextForgeError) as raised:
        Pipeline().add("unknown").compile()
    restored = pickle.loads(pickle.dumps(raised.value))
    assert type(restored) is TextForgeError
    assert restored.code == raised.value.code
    assert restored.stage == raised.value.stage
    assert restored.message == raised.value.message


@pytest.mark.parametrize("document", ["README.md", "docs/builder-api.md"])
def test_documentation_examples(
    document: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import re

    readme = Path(__file__).resolve().parents[1] / document
    examples = re.findall(r"```python\n(.*?)```", readme.read_text(encoding="utf-8"), re.DOTALL)
    assert examples
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {}
    for example in examples:
        exec(compile(example, str(readme), "exec"), namespace)
