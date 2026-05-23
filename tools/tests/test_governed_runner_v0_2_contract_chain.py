from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_governed_runner_v0_2_contract_chain.py"
FIXTURE = ROOT / "tests" / "fixtures" / "chains" / "governed-runner-v0.2-contract-chain.valid.json"


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_governed_runner_v0_2_contract_chain_validates() -> None:
    result = run_validator(FIXTURE)

    assert result.returncode == 0, result.stderr
    assert "OK:" in result.stdout


def test_governed_runner_v0_2_contract_chain_rejects_suspended_authority(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["artifacts"]["authority_state"]["status"] = "suspended"
    candidate = tmp_path / "bad-chain.json"
    candidate.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = run_validator(candidate)

    assert result.returncode == 1
    assert "authority_state must not be suspended" in result.stderr


def test_governed_runner_v0_2_contract_chain_rejects_unblocked_capability(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["blocked_capabilities"]["workspace_mutation"] = False
    candidate = tmp_path / "bad-chain.json"
    candidate.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = run_validator(candidate)

    assert result.returncode == 1
    assert "workspace_mutation" in result.stderr
