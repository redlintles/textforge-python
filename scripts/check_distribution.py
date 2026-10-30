"""Verify wheel contents and the installed package from a consumer's perspective."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

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


def main() -> None:
    """Check every wheel in a directory; optionally type-check an external client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--types", action="store_true")
    args = parser.parse_args()
    wheels = sorted(args.wheel_dir.glob("*.whl"))
    if not wheels:
        raise SystemExit("No wheels found")
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
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

    if textforge.__version__ != importlib.metadata.version("textforgers"):
        raise SystemExit("Native and distribution versions disagree")
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
