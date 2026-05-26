from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP_RUN = ROOT / "tools" / "sp_run.py"
VALIDATOR = ROOT / "tools" / "validate_restore_admission_receipt.py"
CONTRACT = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.valid.json"
RECEIPTS = ROOT / "tests" / "fixtures" / "receipts"


def run_sp_restore_admit(tmp_path: Path, original_context: str, *extra: str) -> dict[str, object]:
    output = tmp_path / "restore-admission.json"
    cmd = [
        sys.executable,
        str(SP_RUN),
        "restore-admit",
        str(CONTRACT),
        "--original-attempt-context",
        str(RECEIPTS / original_context),
        "--requested-restore-action",
        "retry_same_payload",
        "--halt-reason",
        "operator_halt",
        "--verifier-state",
        "passed",
        "--required-budget-usd",
        "0.1",
        "--required-iterations",
        "1",
        "--required-tokens",
        "1000",
        "--generated-at",
        "2026-05-26T18:40:00Z",
        "--output",
        str(output),
        *extra,
    ]
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert result.returncode == 0, result.stderr

    validation = subprocess.run(
        [sys.executable, str(VALIDATOR), str(output)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_restore_admit_queued_none_admits(tmp_path: Path) -> None:
    receipt = run_sp_restore_admit(tmp_path, "original-attempt-context.queued-safe.valid.json")
    assert receipt["recordType"] == "RestoreAdmissionReceipt"
    assert receipt["admitted"] is True
    assert receipt["admission_decision"] == "admit"
    assert receipt["recovery_policy_posture"] == "eligible_for_retry"
    assert "retry_same_payload" in receipt["admitted_actions"]


def test_restore_admit_started_possible_requires_review(tmp_path: Path) -> None:
    receipt = run_sp_restore_admit(tmp_path, "original-attempt-context.started-possible.valid.json")
    assert receipt["admitted"] is False
    assert receipt["admission_decision"] == "require-review"
    assert receipt["recovery_policy_posture"] == "requires_review"
    assert "retry_same_payload" in receipt["blocked_actions"]
    assert "side_effect_boundary=possible" in str(receipt["review_reason"])


def test_restore_admit_completed_confirmed_denies(tmp_path: Path) -> None:
    receipt = run_sp_restore_admit(tmp_path, "original-attempt-context.completed-confirmed.valid.json")
    assert receipt["admitted"] is False
    assert receipt["admission_decision"] == "deny"
    assert receipt["recovery_policy_posture"] == "blocked"
    assert "retry_same_payload" in receipt["blocked_actions"]


def test_restore_admit_stale_verifier_is_review_only(tmp_path: Path) -> None:
    receipt = run_sp_restore_admit(
        tmp_path,
        "original-attempt-context.queued-safe.valid.json",
        "--verifier-state",
        "stale",
    )
    assert receipt["admitted"] is False
    assert receipt["admission_decision"] == "require-review"
    assert "refresh_verifier" in receipt["operator_next_options"]


def test_restore_admit_insufficient_budget_is_review_only(tmp_path: Path) -> None:
    receipt = run_sp_restore_admit(
        tmp_path,
        "original-attempt-context.queued-safe.valid.json",
        "--remaining-budget-usd",
        "0.01",
        "--remaining-iterations",
        "0",
        "--remaining-tokens",
        "10",
    )
    assert receipt["admitted"] is False
    assert receipt["admission_decision"] == "require-review"
    assert "settle_budget" in receipt["operator_next_options"]
