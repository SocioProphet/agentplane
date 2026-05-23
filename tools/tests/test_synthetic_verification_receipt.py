from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "tools" / "build_synthetic_verification_receipt.py"
VALIDATOR = ROOT / "tools" / "validate_verification_execution_receipt.py"


def run_builder(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def base_args(output: Path) -> list[str]:
    return [
        "--output", str(output),
        "--execution-id", "verification-execution-receipt:synthetic-alpha-001",
        "--run-id", "governed-run-alpha-001",
        "--attempt-id", "attempt:governed-run-alpha-001:001",
        "--governed-run-contract-ref", "governed-run-contract:governed-run-alpha-001",
        "--admission-receipt-ref", "attempt-admission-receipt:governed-run-alpha-001:001",
        "--preflight-receipt-ref", "preflight-receipt:governed-run-alpha-001",
        "--authority-state-ref", "agent-authority-current-state:agent-alpha:active",
    ]


def test_synthetic_verification_receipt_builder_writes_valid_receipt(tmp_path: Path) -> None:
    output = tmp_path / "verification-receipt.json"
    result = run_builder(*base_args(output))

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["recordType"] == "VerificationExecutionReceipt"
    assert payload["verifier_command"]["allowlisted"] is True
    assert payload["verifier_command"]["network_mode"] == "off"
    assert payload["verifier_command"]["mutation_mode"] == "none"
    assert payload["receipt_hash"].startswith("sha256:")

    validation = run_validator(output)
    assert validation.returncode == 0, validation.stderr


def test_synthetic_verification_receipt_builder_rejects_rejected_admission(tmp_path: Path) -> None:
    output = tmp_path / "verification-receipt.json"
    result = run_builder(*base_args(output), "--admission-decision", "reject")

    assert result.returncode == 1
    assert "admission_decision must be admit" in result.stderr
    assert not output.exists()


def test_synthetic_verification_receipt_builder_rejects_review_required_preflight(tmp_path: Path) -> None:
    output = tmp_path / "verification-receipt.json"
    result = run_builder(*base_args(output), "--preflight-outcome", "require-review")

    assert result.returncode == 1
    assert "preflight_outcome must be pass" in result.stderr
    assert not output.exists()


def test_synthetic_verification_receipt_builder_rejects_suspended_authority(tmp_path: Path) -> None:
    output = tmp_path / "verification-receipt.json"
    result = run_builder(*base_args(output), "--authority-decision", "suspended")

    assert result.returncode == 1
    assert "authority_decision cannot be suspended or revoked" in result.stderr
    assert not output.exists()
