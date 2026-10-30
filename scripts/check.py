"""Run the binding checks and the complete vendored core pre-commit checklist."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    """Stop immediately if a required check fails."""
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    """Check the installed wheel, typed Python facade, Rust adapter and core."""
    run("cargo", "fmt", "--check")
    run("cargo", "clippy", "--all-targets", "--locked", "--", "-D", "warnings")
    run("cargo", "test", "--locked")
    run(sys.executable, "-m", "ruff", "check", "python", "tests", "scripts")
    run(sys.executable, "-m", "ruff", "format", "--check", "python", "tests", "scripts")
    run(sys.executable, "-m", "mypy", "python", "tests", "scripts")
    run(sys.executable, "-m", "pytest")
    manifest = str(ROOT / "vendor/textforge/Cargo.toml")
    run("cargo", "fmt", "--manifest-path", manifest, "--check")
    for features in (None, "test_access"):
        command = ["cargo", "clippy", "--manifest-path", manifest, "--all-targets", "--locked"]
        if features:
            command.extend(["--features", features])
        run(*command, "--", "-D", "warnings")
    for features in (None, "bytecode", "watchers", "test_access"):
        command = ["cargo", "test", "--manifest-path", manifest, "--locked"]
        if features:
            command.extend(["--features", features])
        run(*command)


if __name__ == "__main__":
    main()
