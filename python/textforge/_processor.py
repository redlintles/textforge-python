"""Typed processor facade over the shared portable engine."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING

from . import _native
from ._arguments import _number
from ._buffers import BufferOptions, PortableBuffer
from ._native import Instruction, TextForgeError
from ._observers import Observers
from ._paths import Path, _path

if TYPE_CHECKING:
    from . import Pipeline


class BatchPool:
    """Reusable batch workers. Close explicitly or use with BatchPool(2)."""

    def __init__(self, threads: int = 0) -> None:
        _number(threads, "threads")
        self._inner = _native.BatchPool(threads)

    @property
    def closed(self) -> bool:
        """Whether worker resources have been released."""
        return self._inner.closed

    def close(self) -> None:
        """Release workers; concurrent close is rejected while borrowed."""
        self._inner.close()

    def __enter__(self) -> BatchPool:
        if self.closed:
            raise ValueError("batch pool is closed")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


@dataclass(frozen=True, slots=True)
class FileTask:
    """One file request with its own pipeline identifier."""

    input: Path
    pipeline_id: str
    output: Path


@dataclass(frozen=True, slots=True)
class BufferTask:
    """One buffered file request; results retain task order."""

    pipeline_id: str
    input: Path


FileRequest = FileTask | tuple[Path, str, Path]


def _file_tasks(
    tasks: Sequence[FileRequest],
) -> list[tuple[_native.FilePath, str, _native.FilePath]]:
    result = []
    for task in tasks:
        input, identifier, output = (
            (task.input, task.pipeline_id, task.output) if isinstance(task, FileTask) else task
        )
        result.append((_path(input), identifier, _path(output)))
    return result


class Processor:
    """Pipeline registry, text execution, and UTF-8 file/bytecode persistence.

    Long-running native operations release the GIL. Concurrent mutable calls on
    the same processor are rejected; use compiled pipelines for shared execution.

    >>> processor = Processor()
    >>> identifier = processor.register(Pipeline().trim_both_sides())
    >>> processor.process_all(identifier, " é ")
    'é'
    """

    def __init__(self) -> None:
        self._inner = _native.Processor()

    def register(self, plan: Pipeline) -> str:
        """Validate and register a snapshot; the source plan stays reusable."""
        return self._inner.register(plan._lower())

    def remove_transform(self, id: str) -> None:
        """Remove an identifier; missing identifiers raise TextForgeError."""
        self._inner.remove_transform(id)

    def transform_exists(self, id: str) -> bool:
        """Return whether an identifier is registered."""
        return self._inner.transform_exists(id)

    def list_transforms(self) -> list[str]:
        """Return a sorted snapshot of registered identifiers."""
        return self._inner.list_transforms()

    def clone_pipeline(self, id: str) -> str:
        """Register an independent copy under a new identifier."""
        return self._inner.clone_pipeline(id)

    def get_transform_vec(self, id: str) -> list[Instruction]:
        """Return independent typed descriptions of the lowered instructions."""
        return self._inner.get_transform_vec(id)

    def process_batch(
        self, tasks: Sequence[FileRequest], *, threads: int = 0
    ) -> list[TextForgeError | None]:
        """Process files in parallel, preserving task order and each task's error.

        Each task is ``(input_path, pipeline_id, output_path)``. A successful
        task returns ``None``; a failed task returns a structured exception.
        Zero threads lets the engine select its worker count. Output paths
        must be distinct to avoid concurrent writes to the same file.
        """
        _number(threads, "threads")
        converted = _file_tasks(tasks)
        return self._inner.process_batch(converted, threads)

    def get_text_transform_vec(self, id: str) -> list[str]:
        """Return canonical textual instructions."""
        return self._inner.get_text_transform_vec(id)

    def process_all(self, id: str, input: str) -> str:
        """Execute a registered pipeline."""
        return self._inner.process_all(id, input)

    def run_transform(self, id: str, input: str) -> str:
        """Execute with an isolated context and no retained error log."""
        return self._inner.run_transform(id, input)

    def process_single(self, instruction: Instruction, input: str) -> str:
        """Execute one instruction without registering a pipeline."""
        return self._inner.process_single(instruction, input)

    def process_all_with_debug(self, id: str, input: str) -> str:
        """Execute and print engine diagnostics to native stdout."""
        return self._inner.process_all_with_debug(id, input)

    def process_single_with_debug(self, instruction: Instruction, input: str) -> str:
        """Execute one instruction and print engine diagnostics."""
        return self._inner.process_single_with_debug(instruction, input)

    def get_pipeline_from_file(self, path: Path) -> str:
        """Import a textual pipeline, accepting str or a text PathLike."""
        return self._inner.get_pipeline_from_file(_path(path))

    def write_pipeline_to_file(self, id: str, path: Path) -> None:
        """Export a registered pipeline to a textual file."""
        self._inner.write_pipeline_to_file(id, _path(path))

    def read_from_bytecode_file(self, path: Path) -> str:
        """Import a TextForge bytecode file."""
        return self._inner.read_from_bytecode_file(_path(path))

    def write_to_bytecode_file(self, id: str, path: Path) -> None:
        """Export a pipeline using the core big-endian bytecode format."""
        self._inner.write_to_bytecode_file(id, _path(path))

    def process_file(self, id: str, input: Path, output: Path) -> None:
        """Transform a UTF-8 file; existing output follows core overwrite semantics."""
        self._inner.process_file(id, _path(input), _path(output))

    def create_pipeline(self) -> Pipeline:
        """Create a reusable plan whose build() registers with this processor."""
        from . import Pipeline

        plan = Pipeline()
        object.__setattr__(plan, "_processor", self)
        return plan

    def add_transform(self, instructions: Sequence[Instruction]) -> str:
        """Validate and register owned instruction descriptions atomically."""
        return self._inner.add_transform(list(instructions))

    def show_transforms(self) -> None:
        """Print registered transforms using the core's native stdout behavior."""
        self._inner.show_transforms()

    def process_batch_in_pool(
        self, pool: BatchPool, tasks: Sequence[FileRequest]
    ) -> list[TextForgeError | None]:
        """Execute ordered file tasks in caller-owned reusable workers."""
        return self._inner.process_batch_in_pool(pool._inner, _file_tasks(tasks))

    def process_all_with_watchers(
        self, id: str, input: str, observers: Observers, report: Path
    ) -> str:
        """Execute synchronously with observers and publish/reset the core report.

        Observer failure preserves an existing report and may retain earlier
        observations. Use observers.reset() before retrying if appropriate.
        """
        observers._check_thread()
        return self._inner.process_all_with_watchers(id, input, observers._inner, _path(report))

    def process_all_buffered(self, id: str, input: PortableBuffer) -> PortableBuffer:
        """Consume input and execute a full pipeline using the buffered core."""
        return PortableBuffer(self._inner.process_all_buffered(id, input._inner))

    def process_single_buffered(self, instruction: str, input: PortableBuffer) -> PortableBuffer:
        """Consume input and execute one textual instruction, as in Rust."""
        return PortableBuffer(self._inner.process_single_buffered(instruction, input._inner))

    def process_file_buffered(
        self, id: str, input: Path, options: BufferOptions | None = None
    ) -> PortableBuffer:
        """Process a UTF-8 file into an owned buffer."""
        return PortableBuffer(
            self._inner.process_file_buffered(id, _path(input), (options or BufferOptions())._inner)
        )

    def process_batch_buffered(
        self, tasks: Sequence[BufferTask], options: BufferOptions | None = None
    ) -> list[PortableBuffer | TextForgeError]:
        """Return one owned buffer or structured error per task, in input order."""
        native = self._inner.process_batch_buffered(
            [(t.pipeline_id, _path(t.input)) for t in tasks], (options or BufferOptions())._inner
        )
        return [
            PortableBuffer(result) if isinstance(result, _native.PortableBuffer) else result
            for result in native
        ]
