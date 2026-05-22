from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP_RUN = ROOT / "tools" / "sp_run.py"
CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.valid.json"
REVIEW_CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.open-network.review.json"


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SP_RUN), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_sp_run_preflight_projects_valid_contract_to_pass() -> None:
    result = run_cmd(
        "preflight",
        str(CONTRACT_FIXTURE),
        "--generated-at",
        "2026-05-22T12:20:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "PreflightReceipt"
    assert payload["mode"] == "readonly_projection"
    assert payload["authoritative_safety_owner"] == "SocioProphet/guardrail-fabric"
    assert payload["outcome"] == "pass"
    assert payload["runtime_action"] == "allow"
    assert payload["findings"] == []
    assert payload["safety_preflight_input"]["verification_commands"]


def test_sp_run_preflight_projects_open_network_to_review() -> None:
    result = run_cmd(
        "preflight",
        str(REVIEW_CONTRACT_FIXTURE),
        "--generated-at",
        "2026-05-22T12:21:00Z",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "PreflightReceipt"
    assert payload["outcome"] == "require-review"
    assert payload["runtime_action"] == "require-review"
    kinds = {finding["kind"] for finding in payload["findings"]}
    assert "open_network_requires_review" in kinds
