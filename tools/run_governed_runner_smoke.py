#!/usr/bin/env python3
"""Run a non-mutating governed-runner smoke path.

The smoke path proves the read-only control spine:

GovernedRunContract -> PreflightReceipt -> AttemptAdmissionReceipt -> evidence folder -> RunDossier

It does not execute agents, run verifier commands, mutate files, restore rollback
state, update authority, or settle budget.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import build_run_dossier
import sp_run

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "governed-run-contract.valid.json"
AUTHORITY_FIXTURE = ROOT / "tests" / "fixtures" / "authority" / "agent-authority-current-state.active.json"
ROLLBACK_BOUNDARY_FIXTURE = ROOT / "tests" / "fixtures" / "receipts" / "rollback-boundary.valid.json"
ROLLBACK_RESULT_FIXTURE = ROOT / "tests" / "fixtures" / "receipts" / "rollback-result.valid.json"
RUNTIME_ATTEMPT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "run-dossier" / "run" / "attempts" / "001" / "runtime-attempt-receipt.json"
VERIFICATION_RESULT_FIXTURE = ROOT / "tests" / "fixtures" / "runs" / "run-dossier" / "run" / "attempts" / "001" / "verification-result.json"


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_fixture(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def build_smoke(output_dir: Path, generated_at: str) -> dict[str, Any]:
    contract = load_object(CONTRACT_FIXTURE)
    authority = load_object(AUTHORITY_FIXTURE)

    preflight = sp_run.build_preflight_receipt(contract, generated_at)
    admission = sp_run.build_attempt_admission_receipt(
        contract,
        preflight,
        authority,
        projected_cost_usd=0.25,
        generated_at=generated_at,
    )

    run_dir = output_dir / "run"
    attempt_dir = run_dir / "attempts" / "001"
    output_dir.mkdir(parents=True, exist_ok=True)

    write_object(run_dir / "governed-run-contract.json", contract)
    write_object(attempt_dir / "preflight-receipt.json", preflight)
    write_object(attempt_dir / "attempt-admission-receipt.json", admission)
    copy_fixture(RUNTIME_ATTEMPT_FIXTURE, attempt_dir / "runtime-attempt-receipt.json")
    copy_fixture(VERIFICATION_RESULT_FIXTURE, attempt_dir / "verification-result.json")
    copy_fixture(ROLLBACK_BOUNDARY_FIXTURE, attempt_dir / "rollback-boundary.json")
    copy_fixture(ROLLBACK_RESULT_FIXTURE, attempt_dir / "rollback-result.json")

    dossier = build_run_dossier.build(run_dir, generated_at)
    write_object(output_dir / "run-dossier.json", dossier)

    summary = {
        "schemaVersion": "agentplane.governed-runner-smoke.v0.1",
        "recordType": "GovernedRunnerSmokeResult",
        "ok": dossier["overall_status"] == "ready" and admission["admitted"] is True,
        "output_dir": str(output_dir),
        "run_dir": str(run_dir),
        "run_id": dossier["run_id"],
        "preflight_outcome": preflight["outcome"],
        "admission_decision": admission["admission_decision"],
        "admitted": admission["admitted"],
        "dossier_status": dossier["overall_status"],
        "missing_receipts": dossier["missing_receipts"],
        "artifacts": {
            "preflight": str(attempt_dir / "preflight-receipt.json"),
            "admission": str(attempt_dir / "attempt-admission-receipt.json"),
            "dossier": str(output_dir / "run-dossier.json"),
        },
        "non_goals": [
            "agent_execution",
            "verifier_execution",
            "file_mutation",
            "rollback_restore",
            "authority_update",
            "budget_settlement",
        ],
    }
    write_object(output_dir / "smoke-result.json", summary)
    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=".socioprophet/smoke/governed-runner")
    parser.add_argument("--generated-at", default="2026-05-22T12:45:00Z")
    args = parser.parse_args(argv)

    try:
        summary = build_smoke(Path(args.output_dir), args.generated_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
