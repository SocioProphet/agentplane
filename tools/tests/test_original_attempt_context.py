from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_original_attempt_context.py"
FIXTURES = ROOT / "tests" / "fixtures" / "receipts"


def run_validator(name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(FIXTURES / name)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_valid_original_attempt_contexts_validate() -> None:
    for name in (
        "original-attempt-context.queued-safe.valid.json",
        "original-attempt-context.started-possible.valid.json",
        "original-attempt-context.completed-confirmed.valid.json",
        "original-attempt-context.unknown-review.valid.json",
    ):
        result = run_validator(name)
        assert result.returncode == 0, result.stderr
        assert "OK:" in result.stdout


def test_invalid_original_attempt_contexts_fail() -> None:
    for name in (
        "original-attempt-context.completed-missing-execution.invalid.json",
        "original-attempt-context.queued-with-execution.invalid.json",
        "original-attempt-context.confirmed-safe-retry.invalid.json",
    ):
        result = run_validator(name)
        assert result.returncode == 1, name
        assert "ERROR:" in result.stderr
