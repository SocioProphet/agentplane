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


def test_sp_run_tool_lists_readonly_tools() -> None:
    result = run_cmd("tool", "list-tools")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerToolList"
    names = {tool["name"] for tool in payload["tools"]}
    assert "governed_runner.doctor" in names
    assert "governed_runner.smoke" in names
    assert "governed_runner.admit" in names
    assert all(tool["mode"] == "readonly" for tool in payload["tools"])


def test_sp_run_tool_calls_doctor() -> None:
    result = run_cmd("tool", "call", "governed_runner.doctor", "--args-json", "{}")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerToolDoctor"
    assert payload["ok"] is True
    assert payload["mode"] == "readonly"
    assert "agent_execution" in payload["non_goals"]


def test_sp_run_tool_rejects_unknown_tool() -> None:
    result = run_cmd("tool", "call", "governed_runner.execute", "--args-json", "{}")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerToolError"
    assert payload["ok"] is False
    assert "unknown governed-runner tool" in payload["error"]
