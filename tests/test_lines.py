"""Logical-line operations through the installed typed Python adapter.

Expected values also have independent native Rust fixtures in test_fluent.py.
"""

from __future__ import annotations

import pytest
from textforge import Instruction, Pipeline, TextForgeError


@pytest.mark.parametrize(
    ("source", "expected"),
    [("", "b"), ("a\n", "a\nb\n"), ("é🍌é\r\n", "é🍌é\r\nb\r\n"), ("\r\n", "\r\nb\r\n")],
)
def test_apl_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().append_line("b").compile()
    generic = Pipeline(Instruction("apl", "b")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), [("a\nb", "b"), ("a\r\nb\r\n", "b\r\n"), ("\n", ""), ("é🍌é", "")]
)
def test_dln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().delete_line(1).compile()
    generic = Pipeline(Instruction("dln", 1)).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_dln_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().delete_line(0).compile()("a\nb")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"), [("a\nb", "a\n"), ("é🍌é\r\nb\r\n", "é🍌é\r\n"), ("\n\n", "\n")]
)
def test_dlna_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().delete_lines_after(1).compile()
    generic = Pipeline(Instruction("dlna", 1)).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_dlna_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().delete_lines_after(0).compile()("a\nb")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"), [("a\nb", "b"), ("a\r\né🍌é\r\n", "é🍌é\r\n"), ("\n\n", "\n")]
)
def test_dlnb_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().delete_lines_before(2).compile()
    generic = Pipeline(Instruction("dlnb", 2)).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_dlnb_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().delete_lines_before(0).compile()("a\nb")
    assert error.value.stage == "execution"
