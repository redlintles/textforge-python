"""Logical-line operations through the installed typed Python adapter.

Expected values also have independent native Rust fixtures in test_fluent.py.
"""

from __future__ import annotations

import pytest
from textforge import Instruction, Pipeline


@pytest.mark.parametrize(
    ("source", "expected"),
    [("", "b"), ("a\n", "a\nb\n"), ("é🍌é\r\n", "é🍌é\r\nb\r\n"), ("\r\n", "\r\nb\r\n")],
)
def test_apl_line_boundaries(source: str, expected: str) -> None:
    fluent = Pipeline().append_line("b").compile()
    generic = Pipeline(Instruction("apl", "b")).compile()
    assert fluent(source) == generic(source) == expected
    assert fluent(source) == expected
