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
    assert "execute" in payload["non_goals"]


def test_python_entrypoint_delegates_to_agentplane_tooling() -> None:
    result = run_cmd(sys.executable, str(ENTRYPOINT), "doctor")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["tool"] == "sp-run"
    assert payload["ok"] is True
    assert "preflight" in payload["capabilities"]
