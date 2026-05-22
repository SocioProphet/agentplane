from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP_RUN = ROOT / "tools" / "sp_run.py"
RUN_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "run-dossier" / "run"
DOSSIER_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "run-dossier" / "run-dossier.valid.json"


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
