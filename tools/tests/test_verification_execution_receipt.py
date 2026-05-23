from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_verification_execution_receipt.py"
FIXTURES = ROOT / "tests" / "fixtures" / "receipts"


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_valid_verification_receipt_validates() -> None:
    result = run_validator(FIXTURES / "verification-execution-receipt.completed.valid.json")

    assert result.returncode == 0, result.stderr
    assert "OK:" in result.stdout


def test_invalid_verification_receipts_fail_closed() -> None:
    for name in (
        "verification-execution-receipt.missing-admission-ref.invalid.json",
        "verification-execution-receipt.rejected-admission.invalid.json",
        "verification-execution-receipt.require-review-admission.invalid.json",
        "verification-execution-receipt.non-allowlisted-command.invalid.json",
        "verification-execution-receipt.open-mode.invalid.json",
        "verification-execution-receipt.write-mode.invalid.json",
    ):
        result = run_validator(FIXTURES / name)
        assert result.returncode == 1, name
        assert "ERROR:" in result.stderr
