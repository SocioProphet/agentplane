from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_execution_timing_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_execution_timing.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "OK: validated" in result.stdout
