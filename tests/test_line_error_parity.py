"""Compare every native line error field with the installed Python adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from textforge import Pipeline, TextForgeError

ROOT = Path(__file__).resolve().parents[1]
REFERENCES: dict[str, Any] = json.loads(
    (ROOT / "tests/fixtures/processor_reference.json").read_text(encoding="utf-8")
)["cases"]
CASES: list[tuple[str, list[str | int], str]] = [
    ("append_line", ["x\ny"], "multiline"),
    ("prepend_line", ["x\ny"], "multiline"),
    ("insert_line", [1, "x\ny"], "multiline"),
    ("replace_line", [1, "x\ny"], "multiline"),
    ("keep_lines_matching", ["["], "regex"),
    ("delete_lines_matching", ["["], "regex"),
]
# Line numbers start at 0 (TextForge 0.3.2): "a\nb" has lines 0 and 1, and an
# interval end past the last line is clamped, so only its start can be missing.
for method in ("delete_line", "delete_lines_after", "delete_lines_before"):
    CASES.extend([(method, [2], "past_end"), (method, [100], "missing")])
CASES.extend(
    [
        ("insert_line", [3, "x"], "past_end"),
        ("insert_line", [100, "x"], "missing"),
        ("replace_line", [2, "x"], "past_end"),
        ("replace_line", [100, "x"], "missing"),
    ]
)
for method in ("select_lines", "delete_lines_interval"):
    CASES.extend(
        [
            (method, [2, 2], "past_end"),
            (method, [100, 101], "missing"),
            (method, [1, 0], "inverted"),
        ]
    )


@pytest.mark.parametrize(("method", "arguments", "failure"), CASES)
def test_native_error_fields(method: str, arguments: list[str | int], failure: str) -> None:
    with pytest.raises(TextForgeError) as caught:
        getattr(Pipeline(), method)(*arguments).compile()("a\nb")
    expected = REFERENCES[f"line_{method}_{failure}"]["error"]
    assert {key: getattr(caught.value, key) for key in expected} == expected
