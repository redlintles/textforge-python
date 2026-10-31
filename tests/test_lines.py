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


@pytest.mark.parametrize(
    ("source", "expected"), [("a\nb\nc", "b\n"), ("a\r\né🍌é\r\nc", "é🍌é\r\n"), ("\n\n", "\n")]
)
def test_slnc_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().select_lines(2, 2).compile()
    generic = Pipeline(Instruction("slnc", 2, 2)).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_slnc_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().select_lines(0, 0).compile()("a\nb")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"), [("a\nb\nc", "a\nc"), ("a\r\né🍌é\r\nc", "a\r\nc"), ("\n\n", "\n")]
)
def test_dlni_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().delete_lines_interval(2, 2).compile()
    generic = Pipeline(Instruction("dlni", 2, 2)).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_dlni_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().delete_lines_interval(0, 0).compile()("a\nb")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"),
    [("a\nb", "a\nx\nb"), ("é🍌é", "é🍌é\nx"), ("a\r\nb\r\n", "a\r\nx\r\nb\r\n"), ("\n", "\nx\n")],
)
def test_inl_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().insert_line(2, "x").compile()
    generic = Pipeline(Instruction("inl", 2, "x")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_inl_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().insert_line(0, "x").compile()("a\nb")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("", ""),
        ("é🍌é", "é🍌é"),
        ("a\r\nb\rc\nd\x0be\x0cf\x85g\u2028h\u2029", "abcdefgh"),
        ("\n\r\n", ""),
    ],
)
def test_nln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().remove_line_breaks().compile()
    generic = Pipeline(Instruction("nln")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), [("a\nb", "a\nx"), ("a\r\nb\r\n", "a\r\nx\r\n"), ("\n\n", "\nx\n")]
)
def test_rln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().replace_line(2, "x").compile()
    generic = Pipeline(Instruction("rln", 2, "x")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_rln_rejects_zero_index() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().replace_line(0, "x").compile()("a\nb")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"), [("", "b"), ("a\r\n", "b\r\na\r\n"), ("é🍌é", "b\né🍌é")]
)
def test_pln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().prepend_line("b").compile()
    generic = Pipeline(Instruction("pln", "b")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [("", ""), ("\n\r\n", ""), (" \n\t\r\n", " \n\t\r\n"), ("é🍌é\r\n\r\nx", "é🍌é\r\nx")],
)
def test_dle_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().delete_empty_lines().compile()
    generic = Pipeline(Instruction("dle")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [("", ""), ("b\r\na\nb", "b\r\nb"), ("a\r\nb\r\n", "b\r\n"), ("é🍌é", "")],
)
def test_klm_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().keep_lines_matching("^b$").compile()
    generic = Pipeline(Instruction("klm", "^b$")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_klm_invalid_regex() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().keep_lines_matching("[").compile()("a")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"),
    [("", ""), ("b\r\na\nb", "a\n"), ("a\r\nb\r\n", "a\r\n"), ("é🍌é", "é🍌é")],
)
def test_dlm_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().delete_lines_matching("^b$").compile()
    generic = Pipeline(Instruction("dlm", "^b$")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_dlm_invalid_regex() -> None:
    with pytest.raises(TextForgeError) as error:
        Pipeline().delete_lines_matching("[").compile()("a")
    assert error.value.stage == "execution"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("\na", "a\n\n"),
        ("", ""),
        ("é🍌é", "é🍌é"),
        ("a\r\nb\nc", "c\r\nb\na"),
        ("a\r\nb\r\n", "b\r\na\r\n"),
        ("\n\n", "\n\n"),
    ],
)
def test_revln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().reverse_lines().compile()
    generic = Pipeline(Instruction("revln")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [("", ""), ("a\r\na\nb", "a\r\nb"), ("é\né\né", "é\né\n"), ("\n\n", "\n"), ("🍌\n🍌", "🍌\n")],
)
def test_uniqln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().unique_lines().compile()
    generic = Pipeline(Instruction("uniqln")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"), [("", ""), ("é🍌é", "é🍌é"), ("a\r\nb\rc\n", "a b c"), ("\n\n", " ")]
)
def test_joinln_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().join_lines(" ").compile()
    generic = Pipeline(Instruction("joinln", " ")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected


def test_posix_classes_after_pipeline_interpolation() -> None:
    keep = Pipeline().keep_lines_matching(r"^\[[:alpha:\]]+$").compile()
    delete = Pipeline().delete_lines_matching(r"^\[[:alpha:\]]+$").compile()
    assert keep("abc\r\n123\nXYZ") == "abc\r\nXYZ"
    assert delete("abc\r\n123\nXYZ") == "123\n"
