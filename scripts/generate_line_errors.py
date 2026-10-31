"""Generate native Rust line-error oracle cases. Run before processor references.

The output is test-only code in examples/processor_reference.rs. --check detects
stale templates. No binding implementation or portable instruction mapping is
used to compute expected errors.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Method, failing arguments. Each fails during native engine execution.
CASES: list[tuple[str, str, str]] = [
    ("append_line", '"x\\ny"', "multiline"),
    ("prepend_line", '"x\\ny"', "multiline"),
    ("insert_line", '1, "x\\ny"', "multiline"),
    ("replace_line", '1, "x\\ny"', "multiline"),
    ("keep_lines_matching", '"["', "regex"),
    ("delete_lines_matching", '"["', "regex"),
]
for _method in ("delete_line", "delete_lines_after", "delete_lines_before"):
    CASES.extend([(_method, "0", "zero"), (_method, "100", "missing")])
for _method in ("insert_line", "replace_line"):
    CASES.extend([(_method, '0, "x"', "zero"), (_method, '100, "x"', "missing")])
for _method in ("select_lines", "delete_lines_interval"):
    CASES.extend(
        [(_method, "0, 1", "zero"), (_method, "1, 100", "missing"), (_method, "2, 1", "inverted")]
    )


def render() -> str:
    """Use the public Rust fluent methods and existing error recorder."""
    source = (ROOT / "vendor/textforge/src/api/mod.rs").read_text(encoding="utf-8")
    output = "    // BEGIN GENERATED LINE ERROR ORACLE\n"
    for method, arguments, failure in CASES:
        if f"fn {method}(" not in source:
            continue
        output += f"""    {{
        let mut native = TextForgeProcessor::new();
        let id = native.create_pipeline().{method}({arguments})?.build()?;
        record("line_{method}_{failure}", native.process_all(&id, "a\\nb")
            .map_err(|error| core_error(ErrorStage::Execution, error)));
    }}
"""
    return output + "    // END GENERATED LINE ERROR ORACLE\n"


def main() -> None:
    """Write or verify the deterministic source template."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "examples/processor_reference.rs"
    current = path.read_text(encoding="utf-8")
    begin = "    // BEGIN GENERATED LINE ERROR ORACLE\n"
    end = "    // END GENERATED LINE ERROR ORACLE\n"
    if begin in current:
        prefix, rest = current.split(begin)
        _, suffix = rest.split(end)
    else:
        index = current.rindex("    Ok(())")
        prefix, suffix = current[:index], current[index:]
    candidate = prefix + render() + suffix
    import subprocess

    candidate = subprocess.check_output(
        ["rustfmt", "--edition", "2024", "--emit", "stdout"], input=candidate, text=True
    )
    if args.check:
        if candidate != current:
            raise SystemExit(
                "Native line error oracle is stale; run scripts/generate_line_errors.py"
            )
    else:
        path.write_text(candidate, encoding="utf-8")


if __name__ == "__main__":
    main()
