#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import validate_verification_execution_receipt

DEFAULT_PLAN_ID = "pytest-sp-run-cli"
VERIFIER_PLANS: dict[str, dict[str, str]] = {
    DEFAULT_PLAN_ID: {
        "verifier_command_ref": "verification-plan:synthetic:pytest-sp-run-cli",
        "command": "python3 -m pytest -q tools/tests/test_sp_run_cli.py",
        "network_mode": "off",
        "mutation_mode": "none",
    }
}


class BuildError(Exception):
    pass


def sha256_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def require(value: str, name: str) -> str:
    if not value:
        raise BuildError(f"{name} is required")
    return value


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    plan = VERIFIER_PLANS.get(args.verifier_plan)
    if plan is None:
        raise BuildError(f"unknown verifier plan: {args.verifier_plan}")
    if args.admission_decision != "admit":
        raise BuildError("admission_decision must be admit")
    if args.preflight_outcome != "pass":
        raise BuildError("preflight_outcome must be pass")
    if args.runtime_action != "allow":
        raise BuildError("runtime_action must be allow")
    if args.authority_decision in {"suspended", "revoked"}:
        raise BuildError("authority_decision cannot be suspended or revoked")
    if plan["network_mode"] != "off":
        raise BuildError("verifier plan must use network_mode=off")
    if plan["mutation_mode"] != "none":
        raise BuildError("verifier plan must use mutation_mode=none")

    artifact_refs = [require(args.stdout_ref, "stdout_ref"), require(args.stderr_ref, "stderr_ref")]
    payload: dict[str, Any] = {
        "schemaVersion": "agentplane.verification-execution-receipt.v0.1",
        "recordType": "VerificationExecutionReceipt",
        "execution_id": require(args.execution_id, "execution_id"),
        "run_id": require(args.run_id, "run_id"),
        "attempt_id": require(args.attempt_id, "attempt_id"),
        "governed_run_contract_ref": require(args.governed_run_contract_ref, "governed_run_contract_ref"),
        "admission_receipt_ref": require(args.admission_receipt_ref, "admission_receipt_ref"),
        "preflight_receipt_ref": require(args.preflight_receipt_ref, "preflight_receipt_ref"),
        "authority_state_ref": require(args.authority_state_ref, "authority_state_ref"),
        "verifier_command_ref": plan["verifier_command_ref"],
        "verifier_command": {
            "command": plan["command"],
            "allowlisted": True,
            "network_mode": plan["network_mode"],
            "mutation_mode": plan["mutation_mode"],
        },
        "safety_context": {
            "admission_decision": args.admission_decision,
            "preflight_outcome": args.preflight_outcome,
            "runtime_action": args.runtime_action,
            "authority_decision": args.authority_decision,
        },
        "execution_status": args.execution_status,
        "started_at": require(args.started_at, "started_at"),
        "ended_at": require(args.ended_at, "ended_at"),
        "exit_code": args.exit_code,
        "stdout_ref": artifact_refs[0],
        "stderr_ref": artifact_refs[1],
        "artifact_refs": artifact_refs,
        "labels": {
            "producer": "synthetic-verifier-receipt",
            "issue": "SocioProphet/agentplane#213",
        },
    }
    payload["receipt_hash"] = sha256_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rc = validate_verification_execution_receipt.main([
        "validate_verification_execution_receipt.py",
        str(output_path),
    ])
    if rc != 0:
        raise BuildError("generated receipt did not validate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a synthetic VerificationExecutionReceipt from fixture refs.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--governed-run-contract-ref", required=True)
    parser.add_argument("--admission-receipt-ref", required=True)
    parser.add_argument("--preflight-receipt-ref", required=True)
    parser.add_argument("--authority-state-ref", required=True)
    parser.add_argument("--verifier-plan", default=DEFAULT_PLAN_ID, choices=sorted(VERIFIER_PLANS))
    parser.add_argument("--admission-decision", default="admit", choices=["admit", "reject", "require-review", "fail-closed"])
    parser.add_argument("--preflight-outcome", default="pass", choices=["pass", "warn", "require-review", "quarantine", "block", "rollback", "revoke"])
    parser.add_argument("--runtime-action", default="allow", choices=["allow", "warn", "require-review", "quarantine", "block", "rollback", "revoke"])
    parser.add_argument("--authority-decision", default="unchanged", choices=["unchanged", "reduced", "suspended", "revoked"])
    parser.add_argument("--execution-status", default="completed", choices=["completed", "failed", "skipped", "fail-closed"])
    parser.add_argument("--started-at", default="2026-05-22T13:40:00Z")
    parser.add_argument("--ended-at", default="2026-05-22T13:40:01Z")
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--stdout-ref", default="artifact:synthetic-verifier:stdout")
    parser.add_argument("--stderr-ref", default="artifact:synthetic-verifier:stderr")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = build_receipt(args)
        output_path = Path(args.output)
        validate_payload(payload, output_path)
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: wrote synthetic VerificationExecutionReceipt to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
