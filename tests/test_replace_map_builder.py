"""Scoped map construction and the reported debug/block regression."""

from pathlib import Path

import pytest
from textforge import Pipeline, Processor, ReplaceMapBuilder, TextForgeError


def rules(builder: ReplaceMapBuilder) -> None:
    builder.add_replace("a", "b").add_replace("o", "x").add_replace("e", "t").end()


def test_scoped_map_debug_and_persistence(tmp_path: Path) -> None:
    base = (
        Pipeline()
        .trim_both_sides()
        .add_to_beginning("Banana ")
        .add_to_end("!")
        .block_assoc(
            "banana", Pipeline().to_reverse().to_lowercase_all().replace_all_with("a", "o")
        )
        .normalize_unicode("nfc")
        .call_block("banana")
        .add_to_end("banana laranja fogo vermelho do inferno")
    )
    expected = "!tiurf xnxnxbbbnbnb lbrbnjb fxgx vtrmtlhx dx inftrnx"
    processor = Processor()
    for plan in (
        base.define_replace_map("rmap1", rules).execute_replace_map("rmap1"),
        base.define_replace_map("rmap1", "a", "b")
        .define_replace_map("rmap1", "o", "x")
        .define_replace_map("rmap1", "e", "t")
        .execute_replace_map("rmap1"),
    ):
        identifier = processor.register(plan)
        assert processor.process_all(identifier, "Fruit") == expected
        assert processor.process_all_with_debug(identifier, "Fruit") == expected
        for extension in ("textforge", "textforgebc"):
            destination = tmp_path / f"pipeline.{extension}"
            destination.touch()
            if extension == "textforge":
                processor.write_pipeline_to_file(identifier, destination)
                restored = processor.get_pipeline_from_file(destination)
            else:
                processor.write_to_bytecode_file(identifier, destination)
                restored = processor.read_from_bytecode_file(destination)
            assert processor.process_all_with_debug(restored, "Fruit") == expected


def test_configuration_is_scoped_and_end_does_not_end_pipeline() -> None:
    captured: list[ReplaceMapBuilder] = []

    def configure(builder: ReplaceMapBuilder) -> None:
        captured.append(builder)
        builder.add_replace("cat", "wolf").add_replace("wolf", "dog").end()

    original = Pipeline().add_to_end("!")
    configured = original.define_replace_map("animals", configure).execute_replace_map("animals")
    assert configured.compile().process("cat wolf") == "wolf dog!"
    assert original.compile().process("cat wolf") == "cat wolf!"
    with pytest.raises(TypeError, match="closed"):
        captured[0].add_replace("dog", "cat")
    with pytest.raises(TypeError, match="closed"):
        captured[0].end()


def test_invalid_configuration_is_atomic() -> None:
    original = Pipeline().add_to_end("!")

    def unfinished(builder: ReplaceMapBuilder) -> None:
        builder.add_replace("a", "b")

    def failed(builder: ReplaceMapBuilder) -> None:
        builder.add_replace("a", "b")
        raise ValueError("callback failed")

    with pytest.raises(TypeError, match="end"):
        original.define_replace_map("m", unfinished)
    with pytest.raises(ValueError, match="callback failed"):
        original.define_replace_map("m", failed)
    with pytest.raises(TextForgeError) as error:
        original.define_replace_map("m", lambda builder: builder.end()).compile()
    assert error.value.stage == "validation"
    assert original.compile().process("a") == "a!"
