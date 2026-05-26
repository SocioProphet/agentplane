from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP_RUN = ROOT / "tools" / "sp_run.py"
RUN_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "run-dossier" / "run"
DOSSIER_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "run-dossier" / "run-dossier.valid.json"
RESTORE_ADMISSION_FIXTURE = ROOT / "tests" / "fixtures" / "receipts" / "restore-admission-receipt.started-possible-review.valid.json"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SP_RUN), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_sp_run_doctor_reports_readonly_capabilities() -> None:
    result = run_cmd("doctor")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["tool"] == "sp-run"
    assert payload["mode"] == "readonly"
    assert payload["ok"] is True
    assert "execute" in payload["non_goals"]
    assert "dossier" in payload["capabilities"]


def test_sp_run_dossier_builds_ready_dossier() -> None:
    result = run_cmd(
        "dossier",
        str(RUN_FIXTURE),
        "--generated-at",
        "2026-05-22T12:10:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "RunDossier"
    assert payload["overall_status"] == "ready"
    assert payload["missing_receipts"] == []
    assert payload["latest_admission"]["admitted"] is True


def test_sp_run_dossier_projects_restore_admission_panel(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    shutil.copytree(RUN_FIXTURE, run_dir)
    restore_target = run_dir / "attempts" / "001" / "restore-admission-receipt.json"
    restore_target.write_text(RESTORE_ADMISSION_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    result = run_cmd(
        "dossier",
        str(run_dir),
        "--generated-at",
        "2026-05-26T20:35:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    panel = payload["latest_restore_admission"]
    assert panel["receipt_ref"] == "restore-admission-receipt:started-possible-review-001"
    assert panel["admitted"] is False
    assert panel["admission_decision"] == "require-review"
    assert panel["halt_reason"] == "timeout"
    assert panel["verifier_state"] == "passed"
    assert panel["side_effect_boundary"] == "possible"
    assert "retry_same_payload" in panel["blocked_actions"]
    assert "review_original_attempt" in panel["operator_next_options"]
    assert "restore-admission-receipt:started-possible-review-001" in payload["receipt_refs"]


def test_sp_run_validate_dossier_accepts_valid_fixture() -> None:
    result = run_cmd("validate-dossier", str(DOSSIER_FIXTURE))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_sp_run_validate_dossier_rejects_missing_file() -> None:
    result = run_cmd("validate-dossier", "missing-dossier.json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
