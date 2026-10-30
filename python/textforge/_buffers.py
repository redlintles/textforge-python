"""Explicitly owned UTF-8 buffers and synchronous binary stream protocols."""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import gettempdir
from types import TracebackType
from typing import Protocol

from . import _native
from ._arguments import _number
from ._paths import Path, _path


class StreamReader(Protocol):
    """Synchronous binary input. Return at most maximum bytes, or b'' for EOF."""

    def read(self, maximum: int, /) -> bytes:
        """Read a bounded chunk; chunks may split UTF-8 characters."""
        ...


class StreamWriter(Protocol):
    """Synchronous binary output. Return the number of bytes accepted."""

    def write(self, data: bytes, /) -> int:
        """Write zero or more bytes; the core retries partial writes."""
        ...


@dataclass(frozen=True, slots=True)
class BufferOptions:
    """Per-buffer placement threshold, not a process memory limit.

    >>> BufferOptions(memory_threshold=1024).memory_threshold
    1024
    """

    memory_threshold: int = 1024 * 1024
    spill_directory: Path = field(default_factory=gettempdir)
    _inner: _native.BufferOptions = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        _number(self.memory_threshold, "memory_threshold")
        object.__setattr__(
            self,
            "_inner",
            _native.BufferOptions(self.memory_threshold, _path(self.spill_directory)),
        )


class PortableBuffer:
    """Owned UTF-8 spool; close explicitly or use a context manager.

    Processing and into_string consume the input, including on failure. All
    aliases subsequently report closed and reject access. Reads use byte offsets.

    >>> buffer = PortableBuffer.from_text("é")
    >>> buffer.read_at(0, 2)
    b'\\xc3\\xa9'
    >>> buffer.into_string()
    'é'
    >>> buffer.closed
    True
    """

    def __init__(self, inner: _native.PortableBuffer) -> None:
        self._inner = inner

    @classmethod
    def from_text(cls, text: str, options: BufferOptions | None = None) -> PortableBuffer:
        """Create a buffer from Unicode text."""
        return cls(_native.PortableBuffer.from_text(text, (options or BufferOptions())._inner))

    @classmethod
    def from_file(cls, path: Path, options: BufferOptions | None = None) -> PortableBuffer:
        """Read a native-path UTF-8 file without full-string conversion."""
        return cls(
            _native.PortableBuffer.from_file(_path(path), (options or BufferOptions())._inner)
        )

    @classmethod
    def from_reader(
        cls, reader: StreamReader, options: BufferOptions | None = None
    ) -> PortableBuffer:
        """Read a borrowed binary stream synchronously; the caller owns and closes it."""
        return cls(_native.PortableBuffer.from_reader(reader, (options or BufferOptions())._inner))

    def len_bytes(self) -> int:
        """Return the UTF-8 byte length."""
        return self._inner.len_bytes()

    def is_empty(self) -> bool:
        """Return whether the buffer has no bytes."""
        return self._inner.is_empty()

    def is_spilled(self) -> bool:
        """Return whether the spool has moved to a temporary file."""
        return self._inner.is_spilled()

    def spill(self) -> None:
        """Explicitly move storage to a temporary file."""
        self._inner.spill()

    def read_at(self, offset: int, maximum: int) -> bytes:
        """Read at most maximum bytes; byte ranges can split Unicode characters."""
        _number(offset, "offset")
        _number(maximum, "maximum")
        return self._inner.read_at(offset, maximum)

    def copy_to(self, writer: StreamWriter) -> int:
        """Copy to a borrowed binary stream, retaining this buffer."""
        return self._inner.copy_to(writer)

    def write_to_file(self, path: Path) -> int:
        """Create or overwrite a document, retaining this buffer."""
        return self._inner.write_to_file(_path(path))

    def into_string(self) -> str:
        """Consume the buffer and explicitly materialize all text."""
        return self._inner.into_string()

    @property
    def closed(self) -> bool:
        """Whether storage has been released or transferred."""
        return self._inner.closed

    def close(self) -> None:
        """Release storage; repeated close calls are harmless."""
        self._inner.close()

    def __enter__(self) -> PortableBuffer:
        self.len_bytes()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
