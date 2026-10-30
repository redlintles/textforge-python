"""Lossless conversion of Python filesystem values to the shared native path API."""

from __future__ import annotations

import os
from typing import TypeAlias

from ._native import FilePath

Path: TypeAlias = str | bytes | os.PathLike[str] | os.PathLike[bytes] | FilePath


def _path(value: Path) -> FilePath:
    if isinstance(value, FilePath):
        return value
    raw = os.fspath(value)
    if os.name != "nt":
        return FilePath.from_native_bytes(os.fsencode(raw))
    if isinstance(raw, bytes):
        raw = os.fsdecode(raw)
    encoded = raw.encode("utf-16-le", errors="surrogatepass")
    return FilePath.from_windows_wide(
        [int.from_bytes(encoded[i : i + 2], "little") for i in range(0, len(encoded), 2)]
    )
