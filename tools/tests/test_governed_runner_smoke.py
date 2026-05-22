from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / "tools" / "run_governed_runner_smoke.py"


def test_governed_runner_smoke_builds_receipt_derived_dossier(tmp_path: Path) -> None:
    output_dir = tmp_path / "governed-runner-smoke"
    result = subprocess.run(
        [
            sys.executable,
            str(SMOKE),
            "--output-dir",
            str(output_dir),
            "--generated-at",
            "2026-05-22T12:45:00Z",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["recordType"] == "GovernedRunnerSmokeResult"
    assert summary["ok"] is True
    assert summary["preflight_outcome"] == "pass"
    assert summary["admission_decision"] == "admit"
    assert summary["admitted"] is True
    assert summary["dossier_status"] == "ready"
    assert summary["missing_receipts"] == []
    assert "agent_execution" in summary["non_goals"]

    run_dir = output_dir / "run"
    attempt_dir = run_dir / "attempts" / "001"
    assert (run_dir / "governed-run-contract.json").exists()
    assert (attempt_dir / "preflight-receipt.json").exists()
    assert (attempt_dir / "attempt-admission-receipt.json").exists()
    assert (attempt_dir / "runtime-attempt-receipt.json").exists()
    assert (attempt_dir / "verification-result.json").exists()
    assert (attempt_dir / "rollback-boundary.json").exists()
    assert (attempt_dir / "rollback-result.json").exists()
    assert (output_dir / "run-dossier.json").exists()
    assert (output_dir / "smoke-result.json").exists()

    dossier = json.loads((output_dir / "run-dossier.json").read_text(encoding="utf-8"))
    assert dossier["recordType"] == "RunDossier"
    assert dossier["overall_status"] == "ready"
    assert dossier["latest_admission"]["admitted"] is True
