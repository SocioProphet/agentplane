from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP_RUN = ROOT / "tools" / "sp_run.py"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SP_RUN), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def build_smoke(tmp_path: Path) -> Path:
    output_dir = tmp_path / "smoke-output"
    result = run_cmd(
        "smoke",
        "--output-dir",
        str(output_dir),
        "--generated-at",
        "2026-05-22T12:45:00Z",
    )
    assert result.returncode == 0, result.stderr
    return output_dir / "run"


def test_sp_run_list_reads_run_store(tmp_path: Path) -> None:
    run_dir = build_smoke(tmp_path)
    runs_root = run_dir.parent

    result = run_cmd("list", "--runs-root", str(runs_root))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "RunList"
    assert payload["count"] == 1
    assert payload["runs"][0]["overall_status"] == "ready"
    assert payload["runs"][0]["missing_receipts"] == []


def test_sp_run_status_summarizes_one_run(tmp_path: Path) -> None:
    run_dir = build_smoke(tmp_path)

    result = run_cmd("status", str(run_dir))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "RunStatus"
    assert payload["overall_status"] == "ready"
    assert payload["latest_admission"]["admitted"] is True
    assert payload["latest_rollback"]["status"] == "restored"


def test_sp_run_inspect_reports_receipt_set(tmp_path: Path) -> None:
    run_dir = build_smoke(tmp_path)

    result = run_cmd("inspect", str(run_dir))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "RunInspection"
    assert payload["dossier"]["overall_status"] == "ready"
    assert "attempts/001/attempt-admission-receipt.json" in payload["receipt_files"]
    assert "attempts/001/preflight-receipt.json" in payload["receipt_files"]
    assert "agent_execution" in payload["non_goals"]
