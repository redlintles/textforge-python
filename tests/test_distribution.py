"""Release checks must reject stale artifacts even when a valid wheel is installed."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("name", "version"), [("textforgers", "0.0.0"), ("unrelated", "0.1.2")])
def test_distribution_check_rejects_wrong_metadata(tmp_path: Path, name: str, version: str) -> None:
    wheel = tmp_path / f"{name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"{name}-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n\n",
        )
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_distribution.py"), "--wheel-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Wheel metadata does not match source textforgers" in result.stderr
