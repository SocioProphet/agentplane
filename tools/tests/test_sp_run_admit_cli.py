from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP_RUN = ROOT / "tools" / "sp_run.py"
CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.valid.json"
REVIEW_CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.open-network.review.json"
ACTIVE_AUTHORITY = ROOT / "tests" / "fixtures" / "authority" / "agent-authority-current-state.active.json"
SUSPENDED_AUTHORITY = ROOT / "tests" / "fixtures" / "authority" / "agent-authority-current-state.suspended.json"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SP_RUN), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def preflight_payload(contract: Path, timestamp: str) -> dict[str, object]:
    result = run_cmd("preflight", str(contract), "--generated-at", timestamp)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def write_json(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_sp_run_admit_allows_active_authority_and_passed_preflight(tmp_path: Path) -> None:
    preflight = write_json(
        tmp_path,
        "preflight.json",
        preflight_payload(CONTRACT_FIXTURE, "2026-05-22T12:20:00Z"),
    )
    result = run_cmd(
        "admit",
        str(CONTRACT_FIXTURE),
        "--preflight",
        str(preflight),
        "--authority-state",
        str(ACTIVE_AUTHORITY),
        "--projected-cost-usd",
        "0.25",
        "--generated-at",
        "2026-05-22T12:30:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "AttemptAdmissionReceipt"
    assert payload["admitted"] is True
    assert payload["admission_decision"] == "admit"
    assert payload["reason_code"] == "all_pre_execution_gates_passed"
    assert payload["authority_decision"] == "unchanged"
    assert payload["runtime_action"] == "allow"


def test_sp_run_admit_rejects_suspended_authority(tmp_path: Path) -> None:
    preflight = write_json(
        tmp_path,
        "preflight.json",
        preflight_payload(CONTRACT_FIXTURE, "2026-05-22T12:20:00Z"),
    )
    result = run_cmd(
        "admit",
        str(CONTRACT_FIXTURE),
        "--preflight",
        str(preflight),
        "--authority-state",
        str(SUSPENDED_AUTHORITY),
        "--projected-cost-usd",
        "0.25",
        "--generated-at",
        "2026-05-22T12:31:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["admitted"] is False
    assert payload["admission_decision"] == "reject"
    assert payload["reason_code"] == "authority_suspended"
    assert payload["authority_decision"] == "suspended"


def test_sp_run_admit_routes_review_preflight_to_require_review(tmp_path: Path) -> None:
    preflight = write_json(
        tmp_path,
        "preflight-review.json",
        preflight_payload(REVIEW_CONTRACT_FIXTURE, "2026-05-22T12:21:00Z"),
    )
    result = run_cmd(
        "admit",
        str(REVIEW_CONTRACT_FIXTURE),
        "--preflight",
        str(preflight),
        "--authority-state",
        str(ACTIVE_AUTHORITY),
        "--projected-cost-usd",
        "0.25",
        "--generated-at",
        "2026-05-22T12:32:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["admitted"] is False
    assert payload["admission_decision"] == "require-review"
    assert payload["reason_code"] == "review_required_before_admission"
    assert payload["runtime_action"] == "require-review"


def test_sp_run_admit_rejects_budget_exceed(tmp_path: Path) -> None:
    preflight = write_json(
        tmp_path,
        "preflight.json",
        preflight_payload(CONTRACT_FIXTURE, "2026-05-22T12:20:00Z"),
    )
    result = run_cmd(
        "admit",
        str(CONTRACT_FIXTURE),
        "--preflight",
        str(preflight),
        "--authority-state",
        str(ACTIVE_AUTHORITY),
        "--projected-cost-usd",
        "4.00",
        "--generated-at",
        "2026-05-22T12:33:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["admitted"] is False
    assert payload["admission_decision"] == "reject"
    assert payload["reason_code"] == "projected_cost_exceeds_remaining_budget"
