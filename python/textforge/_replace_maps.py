"""Scoped replacement-map construction; validation and execution stay in Rust."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from ._arguments import _text
from ._native import Variable

TextArgument = str | Variable
ReplaceRule = tuple[TextArgument, TextArgument]


@dataclass(frozen=True, slots=True)
class _ReplaceMapDefinition:
    """Immutable map description retained by a reusable Pipeline."""

    name: TextArgument
    rules: tuple[ReplaceRule, ...]


class ReplaceMapBuilder:
    """Scoped rule collector: ``m.add_replace('cat', 'dog').end()``.

    Edits mutate this short-lived collector, not its parent Pipeline. Callbacks
    run synchronously once during construction; escaped collectors are closed.
    ``end()`` finishes map configuration and never ends pipeline execution.
    """

    __slots__ = ("_rules", "_ended", "_active")

    def __init__(self) -> None:
        self._rules: list[ReplaceRule] = []
        self._ended = False
        self._active = True

    def add_replace(self, pattern: TextArgument, replacement: TextArgument) -> ReplaceMapBuilder:
        """Append one ordered rule; regex semantics remain the core's responsibility."""
        self._check_open()
        self._rules.append((_text(pattern, "pattern"), _text(replacement, "replacement")))
        return self

    def end(self) -> None:
        """Close configuration without executing the map or halting the pipeline."""
        self._check_open()
        self._ended = True

    def _check_open(self) -> None:
        if not self._active or self._ended:
            raise TypeError("replace map configuration is closed")

    def _finish(self) -> tuple[ReplaceRule, ...]:
        if not self._ended:
            raise TypeError("replace map configuration must finish with end()")
        return tuple(self._rules)


ReplaceMapBody = Callable[[ReplaceMapBuilder], None]


def _configure_map(name: TextArgument, configure: ReplaceMapBody) -> _ReplaceMapDefinition:
    builder = ReplaceMapBuilder()
    try:
        result = cast(Callable[[ReplaceMapBuilder], object], configure)(builder)
        if result is not None:
            if inspect.iscoroutine(result):
                result.close()
            raise TypeError("replace map callbacks must be synchronous and return None")
        return _ReplaceMapDefinition(name, builder._finish())
    finally:
        builder._active = False
