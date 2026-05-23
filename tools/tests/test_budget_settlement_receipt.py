from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_budget_settlement_receipt.py"
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


def test_valid_budget_settlement_receipts_validate() -> None:
    for name in (
        "budget-settlement-receipt.settled.valid.json",
        "budget-settlement-receipt.overrun.valid.json",
    ):
        result = run_validator(FIXTURES / name)
        assert result.returncode == 0, result.stderr
        assert "OK:" in result.stdout


def test_invalid_budget_settlement_receipts_fail_closed() -> None:
    for name in (
        "budget-settlement-receipt.missing-admission-ref.invalid.json",
        "budget-settlement-receipt.missing-actuals.invalid.json",
        "budget-settlement-receipt.negative-actual.invalid.json",
        "budget-settlement-receipt.hidden-overrun.invalid.json",
    ):
        result = run_validator(FIXTURES / name)
        assert result.returncode == 1, name
        assert "ERROR:" in result.stderr
