"""Capture independent Rust processor results and complete structured errors."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/processor_reference.json"


def main() -> None:
    """Refresh or verify committed results; all files live in a temporary directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="textforge-processor-reference-") as directory:
        output = subprocess.check_output(
            [
                "cargo",
                "run",
                "--quiet",
                "--locked",
                "--features",
                "test-reference",
                "--example",
                "processor_reference",
                "--",
                directory,
            ],
            cwd=ROOT,
            text=True,
        )
    rows: dict[str, object] = {}
    for line in output.splitlines():
        if not line.startswith("REF\t"):
            continue
        _, name, status, *fields = line.split("\t")
        if status == "ok":
            rows[name] = {"ok": bytes.fromhex(fields[0]).decode()}
        else:
            code, stage, message, instruction, input, kind, cause, hint, ignorable, report = fields
            rows[name] = {
                "error": {
                    "code": int(code),
                    "stage": stage.lower(),
                    "message": bytes.fromhex(message).decode(),
                    "instruction": bytes.fromhex(instruction).decode(),
                    "input": bytes.fromhex(input).decode(),
                    "kind": bytes.fromhex(kind).decode(),
                    "cause": None if cause == "-" else bytes.fromhex(cause).decode(),
                    "hint": None if hint == "-" else bytes.fromhex(hint).decode(),
                    "ignorable": ignorable == "true",
                    "report": bytes.fromhex(report).decode(),
                }
            }
    fixture = (
        json.dumps(
            {
                "core_revision": (ROOT / "vendor/CORE_REVISION")
                .read_text(encoding="utf-8")
                .strip(),
                "cases": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    if args.check:
        if FIXTURE.read_text(encoding="utf-8") != fixture:
            raise SystemExit("Processor reference changed; review before regenerating")
    else:
        FIXTURE.write_text(fixture, encoding="utf-8")
    print(f"Verified {len(rows)} independent processor reference cases")


if __name__ == "__main__":
    main()
