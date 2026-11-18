"""Execution profiles: engine resources and safety limits, never results."""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import _native
from ._arguments import _number

KIB = 1024
GIB = 1024**3


def _limit(value: int | None, parameter: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{parameter} must be a nonnegative int or None (unlimited)")
    if not 0 <= value < 2**64:
        raise OverflowError(f"{parameter} must fit an unsigned 64-bit integer")
    return value


@dataclass(frozen=True, slots=True)
class ExecutionProfile:
    """How the engine spends memory and where it stops runaway work.

    Mirrors Rust ``textforge::api::ExecutionProfile`` and its ``Limits``. The
    spool threshold is the size, in bytes, above which buffered processing keeps
    a document on disk. ``max_generated_bytes`` bounds the text ``rpt``,
    ``padl`` and ``padr`` produce, and ``max_iterations`` the ``iter`` count;
    ``None`` means unlimited. Past a limit an instruction fails with a
    ``LimitExceededError`` (code 31), which ``try_ignore`` never ignores.

    >>> ExecutionProfile.preset("low-memory").spool_threshold
    65536
    >>> ExecutionProfile.balanced().unlimited().max_iterations is None
    True
    """

    spool_threshold: int
    max_generated_bytes: int | None = 2 * GIB
    max_iterations: int | None = 10_000_000

    MIN_SPOOL_THRESHOLD = 4 * KIB
    MAX_SPOOL_THRESHOLD = 64 * GIB

    def __post_init__(self) -> None:
        _number(self.spool_threshold, "spool_threshold")
        _limit(self.max_generated_bytes, "max_generated_bytes")
        _limit(self.max_iterations, "max_iterations")

    @classmethod
    def preset(cls, name: str) -> ExecutionProfile:
        """Return the core preset ``balanced``, ``low-memory`` or ``fast``."""
        if not isinstance(name, str):
            raise TypeError("name must be str")
        return cls(*_native.profile_preset(name))

    @classmethod
    def balanced(cls) -> ExecutionProfile:
        """The default: documents above 1 MiB are spooled."""
        return cls.preset("balanced")

    @classmethod
    def low_memory(cls) -> ExecutionProfile:
        """Spool documents to disk early (64 KiB)."""
        return cls.preset("low-memory")

    @classmethod
    def fast(cls) -> ExecutionProfile:
        """Keep documents in memory up to 256 MiB."""
        return cls.preset("fast")

    def with_limits(
        self, *, max_generated_bytes: int | None, max_iterations: int | None
    ) -> ExecutionProfile:
        """Return a copy with both safety limits replaced (``None`` is unlimited)."""
        return replace(self, max_generated_bytes=max_generated_bytes, max_iterations=max_iterations)

    def unlimited(self) -> ExecutionProfile:
        """Return a copy without safety limits, like Rust ``Limits::unlimited()``."""
        return self.with_limits(max_generated_bytes=None, max_iterations=None)
