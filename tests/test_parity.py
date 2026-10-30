"""Complete surface tracking and independent Rust error/result comparisons."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import textforge
from textforge import (
    BufferOptions,
    Instruction,
    Observers,
    Pipeline,
    PortableBuffer,
    Processor,
    TextForgeError,
    get_var,
)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE: dict[str, Any] = json.loads(
    (ROOT / "tests/fixtures/processor_reference.json").read_text(encoding="utf-8")
)


def test_method_mapping_and_pinned_sources_are_current() -> None:
    mapping = json.loads((ROOT / "docs/api-parity.json").read_text(encoding="utf-8"))
    assert (
        mapping["core_revision"]
        == (ROOT / "vendor/CORE_REVISION").read_text(encoding="utf-8").strip()
    )
    assert REFERENCE["core_revision"] == mapping["core_revision"]
    for path, digest in mapping["source_sha256"].items():
        assert hashlib.sha256((ROOT / "vendor/textforge" / path).read_bytes()).hexdigest() == digest
    source = (ROOT / "vendor/textforge/src/api/mod.rs").read_text(encoding="utf-8")
    builder = set(re.findall(r"^    fn (\w+)", source, re.MULTILINE)) | {"new", "build"}
    source = (ROOT / "vendor/textforge/src/api/processor.rs").read_text(encoding="utf-8")
    trait = source.split("pub trait TextForgeProcessorMethods")[1].split("impl Default")[0]
    processor = set(re.findall(r"^    fn (\w+)", trait, re.MULTILINE)) | {"new", "create_pipeline"}
    source = (
        (ROOT / "vendor/textforge/src/api/processor/buffered.rs")
        .read_text(encoding="utf-8")
        .split("impl TextForgeProcessor {")[1]
    )
    processor |= set(re.findall(r"^    pub fn (\w+)", source, re.MULTILINE))
    source = (ROOT / "vendor/textforge/src/api/processor/file_io.rs").read_text(encoding="utf-8")
    processor |= set(re.findall(r"^    pub fn (\w+)", source, re.MULTILINE))
    assert set(mapping["builder"]) == builder
    assert set(mapping["processor"]) == processor
    for group in (
        "builder",
        "processor",
        "portable_processor",
        "FilePath",
        "PortableBuffer",
        "Observers",
    ):
        for target in mapping[group].values():
            cls, method = target.split(".")
            assert callable(getattr(getattr(textforge, cls), method))


def assert_reference(name: str, operation: Callable[[], str]) -> None:
    expected = REFERENCE["cases"][name]
    if "ok" in expected:
        assert operation() == expected["ok"]
    else:
        with pytest.raises(TextForgeError) as raised:
            operation()
        assert {key: getattr(raised.value, key) for key in expected["error"]} == expected["error"]


def test_processor_results_and_errors_match_rust(tmp_path: Path) -> None:
    processor = Processor()
    id = processor.create_pipeline().add_to_beginning("🍌").add_to_end("é").build()
    assert_reference("unicode", lambda: processor.process_all(id, "e\u0301\0"))
    assert_reference("empty", lambda: processor.process_all(id, ""))
    assert_reference("missing_id", lambda: processor.process_all("missing", "x"))
    assert_reference("missing_snapshot", lambda: str(len(processor.get_transform_vec("missing"))))

    def remove() -> str:
        processor.remove_transform("missing")
        return ""

    assert_reference("missing_remove", remove)
    missing = processor.create_pipeline().repeat(get_var("missing")).build()
    assert_reference("missing_variable", lambda: processor.process_all(missing, "é"))
    regex = processor.create_pipeline().remove_pattern("[").build()
    assert_reference("invalid_regex", lambda: processor.process_all(regex, "é"))
    for name, instruction in [
        ("unknown", Instruction("unknown")),
        ("arity", Instruction("atb")),
        ("parameter_type", Instruction("atb", 1)),
    ]:

        def compile_case(instruction: Instruction = instruction) -> str:
            return Pipeline(instruction).compile()("")

        assert_reference(name, compile_case)
    for name, extension in [("text_roundtrip", "textforge"), ("bytecode_roundtrip", "textforgebc")]:
        path = tmp_path / f"pipeline.{extension}"
        path.touch()
        if name == "text_roundtrip":
            processor.write_pipeline_to_file(id, path)
            restored = processor.get_pipeline_from_file(path)
        else:
            processor.write_to_bytecode_file(id, path)
            restored = processor.read_from_bytecode_file(path)

        def roundtrip(restored: str = restored) -> str:
            return processor.process_all(restored, "x")

        assert_reference(name, roundtrip)
        if name == "text_roundtrip":

            def persist_missing(path: Path = path) -> str:
                processor.write_pipeline_to_file("missing", path)
                return ""

            assert_reference("persistence_missing", persist_missing)
    assert_reference(
        "buffered",
        lambda: processor.process_all_buffered(
            id, PortableBuffer.from_text("x", BufferOptions(1, tmp_path))
        ).into_string(),
    )
    observers = Observers()
    observers.set_builtin("size", "current_len_chars")
    observers.schedule_all("size")
    report = tmp_path / "report.json"
    assert_reference(
        "watched", lambda: processor.process_all_with_watchers(id, "x", observers, report)
    )
    assert_reference("report", lambda: report.read_text(encoding="utf-8"))
    bad = Observers()

    def fail(context: textforge.Observation) -> str:
        raise ValueError("boom")

    bad.set("bad", fail)
    bad.schedule_all("bad")
    single = processor.create_pipeline().add_to_beginning("🍌").build()
    assert_reference(
        "callback_error",
        lambda: processor.process_all_with_watchers(single, "x", bad, tmp_path / "failed.json"),
    )

    def builtin() -> str:
        bad.set_builtin("x", "missing")
        return ""

    assert_reference("builtin_error", builtin)
    import io

    def invalid_utf8() -> str:
        return PortableBuffer.from_reader(
            io.BytesIO(b"\xff"), BufferOptions(1, tmp_path)
        ).into_string()

    assert_reference("invalid_utf8", invalid_utf8)


def test_public_facade_annotations_resolve_at_runtime() -> None:
    import inspect
    from typing import get_type_hints

    for name in textforge.__all__:
        value = getattr(textforge, name)
        if not inspect.isclass(value):
            continue
        for method_name, method in inspect.getmembers(value, inspect.isfunction):
            if not method_name.startswith("_"):
                assert get_type_hints(method), f"Missing annotations on {name}.{method_name}"
