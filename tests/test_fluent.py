"""Fluent Python behavior, including outputs captured from the real Rust builder."""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from typing import Any, get_type_hints

import pytest
from textforge import Instruction, Pipeline, Processor, TextForgeError, Variable, get_var

REFERENCE: list[dict[str, Any]] = json.loads(
    (Path(__file__).parent / "fixtures/builder_reference.json").read_text(encoding="utf-8")
)


def argument(value: object) -> object:
    if not isinstance(value, dict):
        return value
    if "variable" in value:
        return get_var(value["variable"])
    if "body" in value:
        return plan(value["body"])
    if "instruction" in value:
        return plan([value["instruction"]])
    raise AssertionError(f"Unknown fixture argument: {value!r}")


def plan(steps: list[list[Any]]) -> Pipeline:
    result = Pipeline()
    for name, args in steps:
        result = getattr(result, name)(*(argument(value) for value in args))
        assert isinstance(result, Pipeline)
    return result


@pytest.mark.parametrize("case", REFERENCE, ids=[case["name"] for case in REFERENCE])
def test_matches_real_rust_builder(case: dict[str, Any]) -> None:
    expected = case["result"]
    if "error" in expected:
        with pytest.raises(TextForgeError) as raised:
            plan(case["steps"]).compile()(case["input"])
        assert raised.value.code == expected["error"]
    else:
        assert plan(case["steps"]).compile()(case["input"]) == expected["ok"]


def test_complete_rust_builder_surface_has_explicit_typed_methods() -> None:
    root = Path(__file__).resolve().parents[1]
    rust = (root / "vendor/textforge/src/api/mod.rs").read_text(encoding="utf-8")
    names = set(re.findall(r"^    fn (\w+)(?:<[^\n]*>)?\(", rust, re.MULTILINE)) - {"push_token"}
    assert names == {case["name"] for case in REFERENCE}
    for name in names:
        method = getattr(Pipeline, name)
        signature = inspect.signature(method)
        assert all(
            parameter.annotation is not inspect.Parameter.empty
            for key, parameter in signature.parameters.items()
            if key != "self"
        )
        assert signature.return_annotation == "Pipeline"
        assert method.__doc__
    assert list(inspect.signature(Pipeline.insert).parameters) == [
        "self",
        "index",
        "text_to_insert",
    ]
    assert get_type_hints(Pipeline.add_to_beginning)["text"] == str | Variable
    assert get_type_hints(Pipeline.repeat)["times"] == int | Variable


@pytest.mark.parametrize("text", ["", "é", "🍌", "e\u0301"])
def test_intuitive_chain_and_immutable_reuse(text: str) -> None:
    base = Pipeline().add_to_beginning("banana")
    extended = base.delete_first().add_to_end("!")
    assert base.compile()(text) == "banana" + text
    assert extended.compile()(text) == "anana" + text + "!"
    processor = Processor()
    id = processor.register(extended)
    assert processor.process_all(id, text) == extended.compile()(text)


def test_keywords_variables_and_numeric_normalization() -> None:
    pipeline = (
        Pipeline()
        .var(var_name="n", var_value=1)
        .mut_var(var_name="n", var_value=2)
        .val(var_name="suffix", var_value="!")
        .repeat(times=get_var("n"))
        .add_to_end(text=get_var("suffix"))
    )
    assert pipeline.compile()("é") == "éé!"
    assert Pipeline().val("n", 2).repeat(get_var("n")).compile()("x") == "xx"
    assert (
        Pipeline().eval(expr="2 + 3", var_name="n").repeat(get_var("n")).compile()("x") == "xxxxx"
    )
    assert Pipeline().insert(index=0, text_to_insert="🍌").compile()("éx") == "é🍌x"


def test_callback_groups_are_eager_owned_and_reusable() -> None:
    calls = 0

    def body(builder: Pipeline) -> Pipeline:
        nonlocal calls
        calls += 1
        return builder.add_to_end("!")

    source = Pipeline().add_to_beginning("🍌")
    defined = source.block_assoc("suffix", body).call_block(block_name="suffix")
    assert calls == 1
    assert defined.compile()("é") == "🍌é!"
    assert defined.compile()("x") == "🍌x!"
    assert calls == 1
    assert source.compile()("é") == "🍌é"
    conditional = Pipeline().if_do_contains_each(
        "x", lambda b: b.remove_pattern("x").add_to_end("skipped")
    )
    assert conditional.compile()("x") == ""
    assert conditional.compile()("é") == "é"


def test_invalid_callback_and_callback_exception() -> None:
    base = Pipeline().add_to_end("!")
    with pytest.raises(TypeError, match="callback must return a Pipeline"):
        base.block_assoc("x", lambda b: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(TypeError, match="body must be"):
        base.if_do_contains_each("x", 1)  # type: ignore[arg-type]

    def failing(_: Pipeline) -> Pipeline:
        raise LookupError("construction failed")

    with pytest.raises(LookupError, match="construction failed"):
        base.block_assoc("x", failing)
    assert base.compile()("é") == "é!"


def test_iteration_uses_a_single_named_operation() -> None:
    body = Pipeline().add_to_end("!")
    assert Pipeline().iter(2, body).compile()("é") == "é!!"
    assert body.compile()("é") == "é!"
    for invalid in (Pipeline(), body.delete_first(), Pipeline().block_assoc("x", body)):
        with pytest.raises(ValueError, match="exactly one instruction"):
            Pipeline().iter(2, invalid)
    processor = Processor()
    id = processor.register(body)
    snapshot = processor.get_transform_vec(id)[0]
    assert Pipeline().iter(2, snapshot).compile()("é") == "é!!"


def test_named_argument_validation_and_overflow() -> None:
    invalid_text: tuple[object, ...] = (1, True, None, Instruction("tbs"))
    for value in invalid_text:
        with pytest.raises(TypeError, match="text must be str or Variable"):
            Pipeline().add_to_beginning(value)  # type: ignore[arg-type]
    invalid_number: tuple[object, ...] = ("2", True, 1.5, None)
    for value in invalid_number:
        with pytest.raises(TypeError, match="times must be"):
            Pipeline().repeat(value)  # type: ignore[arg-type]
    for value in (-1, 2**64):
        with pytest.raises(OverflowError):
            Pipeline().repeat(value)
        with pytest.raises(OverflowError):
            Pipeline().val("n", value)
    with pytest.raises(TypeError):
        Pipeline().val("n", True)
    with pytest.raises(TypeError):
        Pipeline().iter(2, "atb")  # type: ignore[arg-type]


def test_named_structural_rules_still_validate_atomically() -> None:
    processor = Processor()
    id = processor.register(Pipeline().trim_both_sides())
    invalid = Pipeline().block_assoc(
        "outer", lambda b: b.block_assoc("inner", Pipeline().add_to_end("!"))
    )
    with pytest.raises(TextForgeError) as raised:
        processor.register(invalid)
    assert raised.value.stage == "validation"
    assert processor.list_transforms() == [id]


@pytest.mark.parametrize("value", [1, None, Variable("n")])
def test_group_names_and_patterns_require_text(value: object) -> None:
    with pytest.raises(TypeError):
        Pipeline().block_assoc(value, Pipeline())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Pipeline().if_do_contains_each(value, Pipeline())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Pipeline().call_block(value)  # type: ignore[arg-type]
