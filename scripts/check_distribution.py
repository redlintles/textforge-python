"""Verify wheel contents and the installed package from a consumer's perspective."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources
import re
import subprocess
import sys
import tempfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "textforge/py.typed",
    "textforge/_native.pyi",
    "textforge/__init__.py",
    "textforge/_arguments.py",
    "textforge/_paths.py",
    "textforge/_buffers.py",
    "textforge/_observers.py",
    "textforge/_processor.py",
}

CLIENT = """from textforge import (BatchPool, BufferOptions, BufferTask, FilePath, FileTask,
    Observation, Observers, Pipeline, PortableBuffer, Processor, TextForgeError, features)
processor = Processor()
plan: Pipeline = processor.create_pipeline().add_to_end("!")
identifier: str = plan.build()
native_path: FilePath = FilePath.from_text("file.txt")
options = BufferOptions(memory_threshold=1, spill_directory=".")
buffer: PortableBuffer = PortableBuffer.from_text("é", options)
output: PortableBuffer = processor.process_all_buffered(identifier, buffer)
results: list[PortableBuffer | TextForgeError] = processor.process_batch_buffered(
    [BufferTask(identifier, native_path)], options)
observers = Observers()
def capture(observation: Observation) -> str:
    return observation.current
observers.set("capture", capture)
with BatchPool(2) as pool:
    tasks: list[TextForgeError | None] = processor.process_batch_in_pool(
        pool, [FileTask("input", identifier, "output")])
enabled: bool = features().buffered
"""


def source_version() -> str:
    """Read the binding package version used by maturin's dynamic metadata."""
    manifest = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    package = manifest.split("[package]", 1)[1].split("\n[", 1)[0]
    match = re.search(r'^version\s*=\s*"([^"\n]+)"\s*$', package, re.MULTILINE)
    if match is None:
        raise SystemExit("Cannot determine the source package version")
    return match[1]


def check_metadata(archive: zipfile.ZipFile, expected: str) -> None:
    """Reject stale or unrelated wheels before inspecting their package files."""
    metadata = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
    if len(metadata) != 1:
        raise SystemExit("Wheel must contain exactly one distribution METADATA file")
    headers = BytesParser().parsebytes(archive.read(metadata[0]))
    if headers["Name"] != "textforgers" or headers["Version"] != expected:
        raise SystemExit(
            f"Wheel metadata does not match source textforgers {expected}: "
            f"{headers['Name']} {headers['Version']}"
        )


def main() -> None:
    """Check every wheel in a directory; optionally type-check an external client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--types", action="store_true")
    args = parser.parse_args()
    wheels = sorted(args.wheel_dir.glob("*.whl"))
    if not wheels:
        raise SystemExit("No wheels found")
    expected = source_version()
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            check_metadata(archive, expected)
            names = set(archive.namelist())
            missing = REQUIRED - names
            if missing:
                raise SystemExit(f"Wheel lacks required files: {sorted(missing)}")
            if not any(
                n.startswith("textforge/_native") and n.endswith((".so", ".pyd")) for n in names
            ):
                raise SystemExit("Wheel lacks its native extension")
            if not any("/licenses/" in n and n.endswith("LICENSE") for n in names):
                raise SystemExit("Wheel lacks its license")
    package = importlib.resources.files("textforge")
    for required in REQUIRED:
        if not package.joinpath(required.removeprefix("textforge/")).is_file():
            raise SystemExit(f"Installed package lacks {required}")
    import textforge

    if not (textforge.__version__ == importlib.metadata.version("textforgers") == expected):
        raise SystemExit("Source, native and installed distribution versions disagree")
    if not (
        textforge.features().bytecode
        and textforge.features().watchers
        and textforge.features().buffered
    ):
        raise SystemExit("Installed wheel lacks a required production capability")
    if args.types:
        with tempfile.TemporaryDirectory(prefix="textforge-client-") as directory:
            client = Path(directory) / "client.py"
            client.write_text(CLIENT, encoding="utf-8")
            subprocess.run(
                [sys.executable, "-m", "mypy", "--strict", "--no-incremental", str(client)],
                cwd=directory,
                check=True,
            )
    print(f"Verified {len(wheels)} wheel(s), installed resources and native import")


if __name__ == "__main__":
    main()
