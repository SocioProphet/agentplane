from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN_SP_RUN = ROOT / "bin" / "sp-run"
ENTRYPOINT = ROOT / "src" / "agentplane_cli" / "sp_run.py"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_bin_sp_run_doctor_delegates_to_agentplane_tooling() -> None:
    result = run_cmd("bash", str(BIN_SP_RUN), "doctor")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["tool"] == "sp-run"
    assert payload["mode"] == "readonly"
    assert "admit" in payload["capabilities"]
    assert "smoke" in payload["capabilities"]
    assert "execute" in payload["non_goals"]


def test_python_entrypoint_delegates_to_agentplane_tooling() -> None:
    result = run_cmd(sys.executable, str(ENTRYPOINT), "doctor")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["tool"] == "sp-run"
    assert payload["ok"] is True
    assert "preflight" in payload["capabilities"]
    assert "smoke" in payload["capabilities"]


def test_bin_sp_run_smoke_builds_evidence_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "smoke"
    result = run_cmd(
        "bash",
        str(BIN_SP_RUN),
        "smoke",
        "--output-dir",
        str(output_dir),
        "--generated-at",
        "2026-05-22T12:45:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerSmokeResult"
    assert payload["ok"] is True
    assert payload["dossier_status"] == "ready"
    assert (output_dir / "smoke-result.json").exists()
    assert (output_dir / "run-dossier.json").exists()


def test_python_entrypoint_smoke_builds_evidence_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "entrypoint-smoke"
    result = run_cmd(
        sys.executable,
        str(ENTRYPOINT),
        "smoke",
        "--output-dir",
        str(output_dir),
        "--generated-at",
        "2026-05-22T12:45:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerSmokeResult"
    assert payload["ok"] is True
    assert payload["missing_receipts"] == []
    assert (output_dir / "run" / "attempts" / "001" / "attempt-admission-receipt.json").exists()
