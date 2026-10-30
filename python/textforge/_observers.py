"""Thread-confined observers; scheduling and JSON reports belong to the core."""

from __future__ import annotations

from collections.abc import Callable
from threading import get_ident

from . import _native
from ._native import Observation
from ._paths import Path, _path


class Observers:
    """Retain callbacks until replacement, clear(), or garbage collection.

    Callbacks run synchronously on the calling thread and return strings. Python
    exceptions become structured callback-stage TextForgeError values. Re-entering
    a mutably borrowed processor/observer is rejected. Only schedule_all is
    currently implemented by the core.

    >>> observers = Observers()
    >>> observers.set_builtin("size", "current_len_chars")
    >>> observers.schedule_all("size")
    """

    def __init__(self) -> None:
        self._inner = _native.Observers()
        self._owner = get_ident()

    def _check_thread(self) -> None:
        if get_ident() != self._owner:
            raise RuntimeError("Observers must be used on their creating thread")

    def set(self, name: str, callback: Callable[[Observation], str]) -> None:
        """Register or replace a callback without changing its schedule."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._check_thread()
        self._inner.set(name, callback)

    def set_builtin(self, name: str, metric: str) -> None:
        """Register a core builtin metric by its discoverable name."""
        self._check_thread()
        self._inner.set_builtin(name, metric)

    @staticmethod
    def builtin_names() -> list[str]:
        """Return the shared core's available builtin metrics."""
        return _native.Observers.builtin_names()

    def schedule_all(self, name: str) -> None:
        """Run the registered observer after every instruction."""
        self._check_thread()
        self._inner.schedule_all(name)

    def run(self, observation: Observation) -> None:
        """Manually accumulate one observation using the core's scheduling rules."""
        self._check_thread()
        self._inner.run(observation)

    def write_report(self, path: Path) -> None:
        """Write the core JSON schema without resetting collected results."""
        self._check_thread()
        self._inner.write_report(_path(path))

    def reset(self) -> None:
        """Discard results while preserving callbacks and schedules."""
        self._check_thread()
        self._inner.reset()

    def clear(self) -> None:
        """Release callbacks and discard schedules and accumulated results."""
        self._check_thread()
        self._inner.clear()
