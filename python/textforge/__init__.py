"""Typed, owned construction and execution of TextForge pipelines.

>>> Pipeline().add("atb", "🍌").compile()("é")
'🍌é'
"""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike, fspath
from typing import TypeAlias

from . import _native
from ._native import (
    CompiledPipeline as CompiledPipeline,
)
from ._native import (
    Instruction as Instruction,
)
from ._native import (
    TextForgeError as TextForgeError,
)
from ._native import (
    Variable as Variable,
)
from ._native import (
    __version__ as __version__,
)

Argument: TypeAlias = str | int | Variable | Instruction
Path: TypeAlias = str | PathLike[str]

__all__ = [
    "Argument",
    "CompiledPipeline",
    "Instruction",
    "Pipeline",
    "Processor",
    "TextForgeError",
    "Variable",
    "__version__",
]


@dataclass(frozen=True, slots=True)
class _Group:
    kind: str
    value: str
    body: Pipeline


@dataclass(frozen=True, slots=True, init=False)
class Pipeline:
    """Immutable pipeline plan. Every edit returns a new independent plan.

    Arguments omit DSL literals such as ``assoc``, ``do`` and ``times``.
    String arguments retain TextForge's interpolation rules.

    >>> plan = Pipeline().add("tbs").add("ate", "!")
    >>> plan.compile().process(" é ")
    'é!'
    """

    _nodes: tuple[Instruction | _Group, ...]
    _depth: int

    def __init__(self, *instructions: Instruction) -> None:
        if any(not isinstance(item, Instruction) for item in instructions):
            raise TypeError("Pipeline accepts Instruction objects")
        object.__setattr__(self, "_nodes", instructions)
        object.__setattr__(self, "_depth", 0)

    def _append(self, node: Instruction | _Group) -> Pipeline:
        depth = max(self._depth, node.body._depth + 1) if isinstance(node, _Group) else self._depth
        if depth > 32:
            raise ValueError("pipeline group nesting exceeds 32")
        result = Pipeline()
        object.__setattr__(result, "_nodes", (*self._nodes, node))
        object.__setattr__(result, "_depth", depth)
        return result

    def add(self, name: str, *arguments: Argument) -> Pipeline:
        """Append a canonical mnemonic, checking Python argument types immediately."""
        return self._append(Instruction(name, *arguments))

    def block(self, name: str, body: Pipeline) -> Pipeline:
        """Define a reusable block without consuming or modifying its body."""
        if not isinstance(body, Pipeline):
            raise TypeError("body must be a Pipeline")
        return self._append(_Group("block", name, body))

    def contains_each(self, pattern: str, body: Pipeline) -> Pipeline:
        """Re-evaluate containment before each child, as in the portable Rust API."""
        if not isinstance(body, Pipeline):
            raise TypeError("body must be a Pipeline")
        return self._append(_Group("contains_each", pattern, body))

    def call_block(self, name: str) -> Pipeline:
        """Append a call to a previously defined block."""
        return self.add("cblk", name)

    def _lower(self) -> _native.Plan:
        plan = _native.Plan()
        for node in self._nodes:
            if isinstance(node, Instruction):
                plan.add(node)
            elif node.kind == "block":
                plan.block(node.value, node.body._lower())
            else:
                plan.contains_each(node.value, node.body._lower())
        return plan

    def compile(self) -> CompiledPipeline:
        """Validate atomically and create an executable with fresh context per call."""
        return self._lower().compile()


class Processor:
    """Pipeline registry, text execution, and UTF-8 file/bytecode persistence.

    Long-running native operations release the GIL. Concurrent mutable calls on
    the same processor are rejected; use compiled pipelines for shared execution.

    >>> processor = Processor()
    >>> identifier = processor.register(Pipeline().add("tbs"))
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
        self, tasks: list[tuple[Path, str, Path]], *, threads: int = 0
    ) -> list[TextForgeError | None]:
        """Process files in parallel, preserving task order and each task's error.

        Each task is ``(input_path, pipeline_id, output_path)``. A successful
        task returns ``None``; a failed task returns a structured exception.
        Zero threads lets the engine select its worker count. Output paths
        must be distinct to avoid concurrent writes to the same file.
        """
        converted = [(fspath(input), id, fspath(output)) for input, id, output in tasks]
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
        return self._inner.get_pipeline_from_file(fspath(path))

    def write_pipeline_to_file(self, id: str, path: Path) -> None:
        """Export a registered pipeline to a textual file."""
        self._inner.write_pipeline_to_file(id, fspath(path))

    def read_from_bytecode_file(self, path: Path) -> str:
        """Import a TextForge bytecode file."""
        return self._inner.read_from_bytecode_file(fspath(path))

    def write_to_bytecode_file(self, id: str, path: Path) -> None:
        """Export a pipeline using the core big-endian bytecode format."""
        self._inner.write_to_bytecode_file(id, fspath(path))

    def process_file(self, id: str, input: Path, output: Path) -> None:
        """Transform a UTF-8 file; existing output follows core overwrite semantics."""
        self._inner.process_file(id, fspath(input), fspath(output))
