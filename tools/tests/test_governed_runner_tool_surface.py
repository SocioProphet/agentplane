from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "governed_runner_tool_surface.py"
CONTRACT = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.valid.json"
AUTHORITY = ROOT / "tests" / "fixtures" / "authority" / "agent-authority-current-state.active.json"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_tool_surface_lists_readonly_tools() -> None:
    result = run_tool("list-tools")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerToolList"
    names = {tool["name"] for tool in payload["tools"]}
    assert "governed_runner.doctor" in names
    assert "governed_runner.smoke" in names
    assert "governed_runner.inspect" in names
    assert "governed_runner.admit" in names
    assert all(tool["mode"] == "readonly" for tool in payload["tools"])


def test_tool_surface_smoke_list_status_inspect(tmp_path: Path) -> None:
    output_dir = tmp_path / "tool-smoke"
    smoke = run_tool(
        "call",
        "governed_runner.smoke",
        "--args-json",
        json.dumps({"output_dir": str(output_dir), "generated_at": "2026-05-22T12:45:00Z"}),
    )

    assert smoke.returncode == 0, smoke.stderr
    smoke_payload = json.loads(smoke.stdout)
    assert smoke_payload["recordType"] == "GovernedRunnerSmokeResult"
    assert smoke_payload["ok"] is True

    listed = run_tool(
        "call",
        "governed_runner.list",
        "--args-json",
        json.dumps({"runs_root": str(output_dir)}),
    )
    assert listed.returncode == 0, listed.stderr
    list_payload = json.loads(listed.stdout)
    assert list_payload["recordType"] == "RunList"
    assert list_payload["count"] == 1

    run_dir = output_dir / "run"
    status = run_tool(
        "call",
        "governed_runner.status",
        "--args-json",
        json.dumps({"run_dir": str(run_dir)}),
    )
    assert status.returncode == 0, status.stderr
    status_payload = json.loads(status.stdout)
    assert status_payload["recordType"] == "RunStatus"
    assert status_payload["overall_status"] == "ready"

    inspected = run_tool(
        "call",
        "governed_runner.inspect",
        "--args-json",
        json.dumps({"run_dir": str(run_dir)}),
    )
    assert inspected.returncode == 0, inspected.stderr
    inspect_payload = json.loads(inspected.stdout)
    assert inspect_payload["recordType"] == "RunInspection"
    assert "attempts/001/attempt-admission-receipt.json" in inspect_payload["receipt_files"]


def test_tool_surface_preflight_and_admit(tmp_path: Path) -> None:
    preflight = run_tool(
        "call",
        "governed_runner.preflight",
        "--args-json",
        json.dumps({"contract_json": str(CONTRACT), "generated_at": "2026-05-22T12:20:00Z"}),
    )
    assert preflight.returncode == 0, preflight.stderr
    preflight_payload = json.loads(preflight.stdout)
    assert preflight_payload["recordType"] == "PreflightReceipt"
    assert preflight_payload["outcome"] == "pass"

    preflight_path = tmp_path / "preflight.json"
    preflight_path.write_text(json.dumps(preflight_payload), encoding="utf-8")

    admit = run_tool(
        "call",
        "governed_runner.admit",
        "--args-json",
        json.dumps(
            {
                "contract_json": str(CONTRACT),
                "preflight_json": str(preflight_path),
                "authority_state_json": str(AUTHORITY),
                "projected_cost_usd": 0.25,
                "generated_at": "2026-05-22T12:30:00Z",
            }
        ),
    )
    assert admit.returncode == 0, admit.stderr
    admit_payload = json.loads(admit.stdout)
    assert admit_payload["recordType"] == "AttemptAdmissionReceipt"
    assert admit_payload["admitted"] is True
    assert admit_payload["admission_decision"] == "admit"


def test_tool_surface_unknown_tool_fails() -> None:
    result = run_tool("call", "governed_runner.execute", "--args-json", "{}")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "GovernedRunnerToolError"
    assert payload["ok"] is False
    assert "unknown governed-runner tool" in payload["error"]
