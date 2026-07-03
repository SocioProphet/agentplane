#!/usr/bin/env python3
"""Read-only sp-run CLI for governed-run evidence inspection.

This CLI exposes operator-facing receipt inspection, preflight projection,
admission receipt construction, restore admission receipt construction,
smoke evidence generation, run-store inspection, and the local JSON tool
adapter. It does not run agents, execute verifier commands, mutate governed
files, restore rollback state, retry, resume, settle budget, or change
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_run_dossier
import run_governed_runner_smoke
import run_store_inspection
import validate_governed_run_contract
import validate_run_dossier

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "schemas/runs/governed-run-contract.v0.1.schema.json",
    "schemas/runs/run-dossier.v0.1.schema.json",
    "schemas/receipts/attempt-admission-receipt.v0.1.schema.json",
    "schemas/receipts/preflight-receipt.v0.1.schema.json",
    "schemas/receipts/restore-admission-receipt.v0.1.schema.json",
    "schemas/receipts/rollback-boundary.v0.1.schema.json",
    "schemas/receipts/rollback-result.v0.1.schema.json",
    "tools/build_restore_admission_receipt.py",
    "tools/build_run_dossier.py",
    "tools/governed_runner_tool_surface.py",
    "tools/run_governed_runner_smoke.py",
    "tools/run_store_inspection.py",
    "tools/validate_restore_admission_receipt.py",
    "tools/validate_run_dossier.py",
    "tools/validate_governed_run_contract.py",
)


def _rx(codes: tuple[int, ...]) -> re.Pattern[str]:
    return re.compile("".join(chr(code) for code in codes), re.I)


BLOCK_PATTERNS = (
    _rx((40, 94, 124, 92, 115, 41, 114, 109, 92, 115, 43, 45, 114, 102, 40, 92, 115, 124, 36, 41)),
    _rx((103, 105, 116, 92, 115, 43, 114, 101, 115, 101, 116, 92, 115, 43, 45, 45, 104, 97, 114, 100)),
    _rx((103, 105, 116, 92, 115, 43, 99, 108, 101, 97, 110, 92, 115, 43, 45, 102)),
    _rx((40, 99, 117, 114, 108, 124, 119, 103, 101, 116, 41, 92, 98, 91, 94, 92, 110, 124, 93, 42, 92, 124, 92, 115, 42, 40, 115, 104, 124, 98, 97, 115, 104, 41)),
    _rx((40, 94, 124, 92, 115, 41, 115, 117, 100, 111, 40, 92, 115, 124, 36, 41)),
)
NETWORK_TARGET = re.compile(r"https?://([^/\s\"'`]+)", re.I)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_hash(record: dict[str, Any]) -> str:
    copy = dict(record)
    copy.pop("receipt_hash", None)
    payload = json.dumps(copy, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def command_doctor(_args: argparse.Namespace) -> int:
    files = []
    ok = True
    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        ok = ok and exists
        files.append({"path": rel, "exists": exists})
    emit(
        {
            "tool": "sp-run",
            "mode": "readonly",
            "ok": ok,
            "repo_root": str(ROOT),
            "capabilities": [
                "doctor",
                "smoke",
                "list",
                "status",
                "inspect",
                "dossier",
                "validate-dossier",
                "preflight",
                "admit",
                "restore-admit",
                "tool",
            ],
            "non_goals": [
                "execute",
                "mutate",
                "restore",
                "retry",
                "resume",
                "authority_update",
                "budget_settlement",
            ],
            "files": files,
        }
    )
    return 0 if ok else 1


def command_tool(args: argparse.Namespace) -> int:
    import governed_runner_tool_surface

    return governed_runner_tool_surface.main(list(args.args))


def command_list(args: argparse.Namespace) -> int:
    try:
        emit(run_store_inspection.list_runs(Path(args.runs_root)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def command_status(args: argparse.Namespace) -> int:
    try:
        emit(run_store_inspection.status_for_run(Path(args.run_dir)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    try:
        emit(run_store_inspection.inspect_run(Path(args.run_dir)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def command_dossier(args: argparse.Namespace) -> int:
    try:
        dossier = build_run_dossier.build(Path(args.run_dir), args.generated_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(dossier, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def command_validate_bundle(args: argparse.Namespace) -> int:
    import subprocess
    tool = Path(__file__).parent / "validate_sourceos_bundle.py"
    result = subprocess.run([sys.executable, str(tool), "--bundle", args.bundle])
    return result.returncode


def command_validate_dossier(args: argparse.Namespace) -> int:
    try:
        validate_run_dossier.validate_schema(validate_run_dossier.load_json(validate_run_dossier.SCHEMA))
        validate_run_dossier.validate_dossier(validate_run_dossier.load_json(Path(args.dossier_json)))
    except Exception as exc:  # noqa: BLE001
        emit({"ok": False, "dossier": args.dossier_json, "error": str(exc)})
        return 1
    emit({"ok": True, "dossier": args.dossier_json})
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    try:
        contract = load_json_object(Path(args.contract_json))
        receipt = build_preflight_receipt(contract, args.generated_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def command_admit(args: argparse.Namespace) -> int:
    try:
        contract = load_json_object(Path(args.contract_json))
        preflight = load_json_object(Path(args.preflight_json))
        authority = load_json_object(Path(args.authority_state_json))
        receipt = build_attempt_admission_receipt(
            contract,
            preflight,
            authority,
            projected_cost_usd=args.projected_cost_usd,
            generated_at=args.generated_at,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def command_restore_admit(args: argparse.Namespace) -> int:
    import build_restore_admission_receipt

    return build_restore_admission_receipt.main(list(args.args))


def command_smoke(args: argparse.Namespace) -> int:
    return run_governed_runner_smoke.main(
        [
            "--output-dir",
            args.output_dir,
            "--generated-at",
            args.generated_at,
        ]
    )


def build_preflight_receipt(contract: dict[str, Any], generated_at: str | None = None) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        validate_governed_run_contract.validate_schema_contract(
            validate_governed_run_contract.load_json(validate_governed_run_contract.SCHEMA)
        )
        validate_governed_run_contract.validate_contract(contract)
    except Exception as exc:  # noqa: BLE001
        findings.append({"kind": "contract_invalid", "severity": "block", "message": str(exc)})

    verification_commands = [str(step.get("command", "")) for step in contract.get("verification_plan", []) if isinstance(step, dict)]
    allowed_paths = [str(item) for item in contract.get("allowed_paths", [])]
    denied_paths = [str(item) for item in contract.get("denied_paths", [])]
    network_mode = str(contract.get("network_mode", "off"))
    allowed_network_domains = [str(item).lower() for item in contract.get("allowed_network_domains", [])]
    approval_policy = {key: bool(value) for key, value in (contract.get("approval_policy", {}) or {}).items() if isinstance(key, str)}

    for command in verification_commands:
        if any(pattern.search(command) for pattern in BLOCK_PATTERNS):
            findings.append({"kind": "unsafe_verifier_command", "severity": "block", "message": "verifier command matches a blocked command pattern"})
        if network_mode == "off" and NETWORK_TARGET.search(command):
            findings.append({"kind": "network_blocked", "severity": "block", "message": "network target appears while network_mode=off"})
        if network_mode == "allowlisted":
            for target in NETWORK_TARGET.findall(command):
                target = target.lower()
                if not any(target == domain or target.endswith(f".{domain}") for domain in allowed_network_domains):
                    findings.append({"kind": "network_not_allowlisted", "severity": "block", "message": f"network target is not allowlisted: {target}"})

    if network_mode == "open":
        findings.append({"kind": "open_network_requires_review", "severity": "require-review", "message": "network_mode=open requires review before execution"})

    for path in allowed_paths + denied_paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            findings.append({"kind": "unsafe_path_pattern", "severity": "block", "message": f"path pattern is outside the governed workspace: {path}"})

    if approval_policy.get("external_writes"):
        findings.append({"kind": "external_writes_require_review", "severity": "require-review", "message": "external writes approval flag requires human review before execution"})

    outcome = outcome_from_findings(findings)
    runtime_action = {"pass": "allow", "require-review": "require-review", "block": "block"}[outcome]
    run_id = str(contract.get("run_id", "unknown-run"))
    receipt: dict[str, Any] = {
        "schemaVersion": "agentplane.preflight-receipt.v0.1",
        "recordType": "PreflightReceipt",
        "receipt_id": f"preflight-receipt:{run_id}",
        "run_id": run_id,
        "governed_run_contract_ref": f"governed-run-contract:{run_id}",
        "mode": "readonly_projection",
        "authoritative_safety_owner": "SocioProphet/guardrail-fabric",
        "outcome": outcome,
        "runtime_action": runtime_action,
        "safety_preflight_input": {
            "verification_commands": verification_commands,
            "allowed_paths": allowed_paths,
            "denied_paths": denied_paths,
            "network_mode": network_mode,
            "allowed_network_domains": allowed_network_domains,
            "approval_policy": approval_policy,
        },
        "findings": findings,
        "generated_at": generated_at or now_utc(),
        "labels": {"source": "sp-run-readonly-preflight"},
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def build_attempt_admission_receipt(
    contract: dict[str, Any],
    preflight: dict[str, Any],
    authority: dict[str, Any],
    *,
    projected_cost_usd: float,
    generated_at: str | None = None,
) -> dict[str, Any]:
    run_id = str(contract.get("run_id", preflight.get("run_id", "unknown-run")))
    attempt_id = f"attempt:{run_id}:001"
    authority_status = str(authority.get("authority_status", "suspended"))
    authority_decision = map_authority_status(authority_status)
    runtime_action = str(preflight.get("runtime_action", "block"))
    safety_outcome = str(preflight.get("outcome", "block"))
    budget = contract.get("budget", {}) if isinstance(contract.get("budget"), dict) else {}
    remaining_budget = float(budget.get("max_usd", 0))
    remaining_iterations = int(budget.get("max_iterations", 0))
    remaining_tokens = int(budget.get("max_tokens", 0))

    admitted, admission_decision, reason_code, fail_closed_reason = admission_result(
        projected_cost_usd=projected_cost_usd,
        remaining_budget_usd=remaining_budget,
        remaining_iterations=remaining_iterations,
        remaining_tokens=remaining_tokens,
        safety_outcome=safety_outcome,
        runtime_action=runtime_action,
        authority_decision=authority_decision,
    )

    receipt: dict[str, Any] = {
        "schemaVersion": "agentplane.attempt-admission-receipt.v0.1",
        "recordType": "AttemptAdmissionReceipt",
        "receipt_id": f"attempt-admission-receipt:{run_id}:001",
        "attempt_id": attempt_id,
        "run_id": run_id,
        "governed_run_contract_ref": f"governed-run-contract:{run_id}",
        "admitted": admitted,
        "admission_decision": admission_decision,
        "reason_code": reason_code,
        "safety_preflight_ref": str(preflight.get("receipt_id", f"preflight-receipt:{run_id}")),
        "safety_preflight_outcome": safety_outcome,
        "authority_state_ref": str(authority.get("stateId", "missing:authority-state")),
        "authority_decision": authority_decision,
        "trustops_runtime_action_ref": str(preflight.get("receipt_id", f"preflight-receipt:{run_id}")),
        "runtime_action": runtime_action,
        "budget_estimate": {
            "projected_cost_usd": projected_cost_usd,
            "remaining_budget_usd": remaining_budget,
            "remaining_iterations": remaining_iterations,
            "remaining_tokens": remaining_tokens,
            "estimate_provenance": "estimated",
        },
        "input_refs": {
            "policy_bundle_ref": str(contract.get("policy_bundle_ref", "missing:policy-bundle")),
            "authority_grant_ref": str(contract.get("authority_grant_ref", "missing:authority-grant")),
            "trustops_gate_policy_ref": str(contract.get("trustops_gate_policy_ref", "missing:trustops-gate-policy")),
            "verification_plan_ref": f"verification-plan:{run_id}",
        },
        "issued_at": generated_at or now_utc(),
        "labels": {"source": "sp-run-readonly-admit"},
    }
    if fail_closed_reason:
        receipt["fail_closed_reason"] = fail_closed_reason
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def map_authority_status(status: str) -> str:
    return {
        "active": "unchanged",
        "reduced": "reduced",
        "suspended": "suspended",
        "revoked": "revoked",
    }.get(status, "suspended")


def admission_result(
    *,
    projected_cost_usd: float,
    remaining_budget_usd: float,
    remaining_iterations: int,
    remaining_tokens: int,
    safety_outcome: str,
    runtime_action: str,
    authority_decision: str,
) -> tuple[bool, str, str, str | None]:
    if remaining_iterations <= 0:
        return False, "reject", "no_remaining_iterations", None
    if remaining_tokens <= 0:
        return False, "reject", "no_remaining_tokens", None
    if projected_cost_usd > remaining_budget_usd:
        return False, "reject", "projected_cost_exceeds_remaining_budget", None
    if authority_decision in {"suspended", "revoked"}:
        return False, "reject", f"authority_{authority_decision}", None
    if safety_outcome in {"quarantine", "block", "rollback", "revoke"}:
        return False, "reject", f"safety_{safety_outcome}", None
    if runtime_action in {"quarantine", "block", "rollback", "revoke"}:
        return False, "reject", f"runtime_action_{runtime_action}", None
    if safety_outcome == "require-review" or runtime_action == "require-review":
        return False, "require-review", "review_required_before_admission", None
    if runtime_action not in {"allow", "warn"}:
        return False, "fail-closed", "unknown_runtime_action", "runtime action could not be mapped to an admission decision"
    return True, "admit", "all_pre_execution_gates_passed", None


def outcome_from_findings(findings: list[dict[str, str]]) -> str:
    severities = {finding.get("severity") for finding in findings}
    if "block" in severities:
        return "block"
    if "require-review" in severities:
        return "require-review"
    return "pass"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sp-run")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check read-only governed-run evidence tooling.")
    doctor.set_defaults(func=command_doctor)

    tool = subparsers.add_parser("tool", help="Access the read-only governed-runner JSON tool adapter.")
    tool.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to governed_runner_tool_surface.py")
    tool.set_defaults(func=command_tool)

    smoke = subparsers.add_parser("smoke", help="Build a deterministic governed-runner smoke evidence bundle.")
    smoke.add_argument("--output-dir", default=".socioprophet/smoke/governed-runner")
    smoke.add_argument("--generated-at", default="2026-05-22T12:45:00Z")
    smoke.set_defaults(func=command_smoke)

    list_cmd = subparsers.add_parser("list", help="List governed-run evidence folders.")
    list_cmd.add_argument("--runs-root", default=".socioprophet/runs")
    list_cmd.set_defaults(func=command_list)

    status = subparsers.add_parser("status", help="Summarize one governed-run evidence folder.")
    status.add_argument("run_dir")
    status.set_defaults(func=command_status)

    inspect = subparsers.add_parser("inspect", help="Inspect one governed-run evidence folder and receipt set.")
    inspect.add_argument("run_dir")
    inspect.set_defaults(func=command_inspect)

    preflight = subparsers.add_parser("preflight", help="Project a governed run contract into a read-only preflight receipt.")
    preflight.add_argument("contract_json")
    preflight.add_argument("--generated-at")
    preflight.add_argument("--output")
    preflight.set_defaults(func=command_preflight)

    admit = subparsers.add_parser("admit", help="Build a read-only AttemptAdmissionReceipt from contract, preflight, and authority state.")
    admit.add_argument("contract_json")
    admit.add_argument("--preflight", dest="preflight_json", required=True)
    admit.add_argument("--authority-state", dest="authority_state_json", required=True)
    admit.add_argument("--projected-cost-usd", type=float, default=0.0)
    admit.add_argument("--generated-at")
    admit.add_argument("--output")
    admit.set_defaults(func=command_admit)

    restore_admit = subparsers.add_parser(
        "restore-admit",
        help="Build a read-only RestoreAdmissionReceipt from contract and OriginalAttemptContext.",
    )
    restore_admit.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to build_restore_admission_receipt.py")
    restore_admit.set_defaults(func=command_restore_admit)

    dossier = subparsers.add_parser("dossier", help="Build a RunDossier from a governed run folder.")
    dossier.add_argument("run_dir")
    dossier.add_argument("--generated-at")
    dossier.add_argument("--output")
    dossier.set_defaults(func=command_dossier)

    validate = subparsers.add_parser("validate-dossier", help="Validate a RunDossier JSON file.")
    validate.add_argument("dossier_json")
    validate.set_defaults(func=command_validate_dossier)

    validate_bundle = subparsers.add_parser("validate-bundle", help="Validate a SourceOS image-production bundle against blocking conditions.")
    validate_bundle.add_argument("--bundle", required=True, help="Path to bundle.json")
    validate_bundle.set_defaults(func=command_validate_bundle)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
