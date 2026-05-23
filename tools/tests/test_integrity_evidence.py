from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools" / "check_integrity_evidence.py"
FIXTURES = ROOT / "tests" / "fixtures" / "receipts"


def run_checker(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_valid_integrity_evidence_records_validate() -> None:
    for name in (
        "integrity-evidence-request.valid.json",
        "integrity-evidence-result.valid.json",
    ):
        result = run_checker(FIXTURES / name)
        assert result.returncode == 0, result.stderr
        assert "OK:" in result.stdout


def test_invalid_integrity_evidence_records_fail() -> None:
    for name in (
        "integrity-evidence-request.missing-boundary.invalid.json",
        "integrity-evidence-request.path-outside-root.invalid.json",
        "integrity-evidence-request.suspended-authority.invalid.json",
    ):
        result = run_checker(FIXTURES / name)
        assert result.returncode == 1, name
        assert "ERROR:" in result.stderr
