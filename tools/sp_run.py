#!/usr/bin/env python3
"""Read-only sp-run CLI for governed-run evidence inspection.

This CLI exposes operator-facing receipt inspection and preflight projection.
It does not run agents, execute verifier commands, mutate files, restore rollback
state, settle budget, or change authority.
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
import validate_governed_run_contract
import validate_run_dossier

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "schemas/runs/governed-run-contract.v0.1.schema.json",
    "schemas/runs/run-dossier.v0.1.schema.json",
    "schemas/receipts/attempt-admission-receipt.v0.1.schema.json",
    "schemas/receipts/preflight-receipt.v0.1.schema.json",
    "schemas/receipts/rollback-boundary.v0.1.schema.json",
    "schemas/receipts/rollback-result.v0.1.schema.json",
    "tools/build_run_dossier.py",
    "tools/validate_run_dossier.py",
    "tools/validate_governed_run_contract.py",
)

BLOCK_PATTERNS = (
    re.compile(r"(^|\s)rm\s+-rf(\s|$)", re.I),
    re.compile(r"git\s+reset\s+--hard", re.I),
    re.compile(r"git\s+clean\s+-f", re.I),
    re.compile(r"(curl|wget)\b[^\n|]*\|\s*(sh|bash)", re.I),
    re.compile(r"(^|\s)sudo(\s|$)", re.I),
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
            "capabilities": ["doctor", "dossier", "validate-dossier", "preflight"],
            "non_goals": ["execute", "mutate", "restore", "authority_update", "budget_settlement"],
            "files": files,
        }
    )
    return 0 if ok else 1


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


def build_preflight_receipt(contract: dict[str, Any], generated_at: str | None = None) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        validate_governed_run_contract.validate_schema_contract(
            validate_governed_run_contract.load_json(validate_governed_run_contract.SCHEMA)
        )
        validate_governed_run_contract.validate_contract(contract)
    except Exception as exc:  # noqa: BLE001
        findings.append(
            {
                "kind": "contract_invalid",
                "severity": "block",
                "message": str(exc),
            }
        )

    verification_commands = [
        str(step.get("command", ""))
        for step in contract.get("verification_plan", [])
        if isinstance(step, dict)
    ]
    allowed_paths = [str(item) for item in contract.get("allowed_paths", [])]
    denied_paths = [str(item) for item in contract.get("denied_paths", [])]
    network_mode = str(contract.get("network_mode", "off"))
    allowed_network_domains = [str(item).lower() for item in contract.get("allowed_network_domains", [])]
    approval_policy = {
        key: bool(value)
        for key, value in (contract.get("approval_policy", {}) or {}).items()
        if isinstance(key, str)
    }

    for command in verification_commands:
        if any(pattern.search(command) for pattern in BLOCK_PATTERNS):
            findings.append(
                {
                    "kind": "unsafe_verifier_command",
                    "severity": "block",
                    "message": "verifier command matches a blocked command pattern",
                }
            )
        if network_mode == "off" and NETWORK_TARGET.search(command):
            findings.append(
                {
                    "kind": "network_blocked",
                    "severity": "block",
                    "message": "network target appears while network_mode=off",
                }
            )
        if network_mode == "allowlisted":
            for target in NETWORK_TARGET.findall(command):
                target = target.lower()
                if not any(target == domain or target.endswith(f".{domain}") for domain in allowed_network_domains):
                    findings.append(
                        {
                            "kind": "network_not_allowlisted",
                            "severity": "block",
                            "message": f"network target is not allowlisted: {target}",
                        }
                    )

    if network_mode == "open":
        findings.append(
            {
                "kind": "open_network_requires_review",
                "severity": "require-review",
                "message": "network_mode=open requires review before execution",
            }
        )

    for path in allowed_paths + denied_paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            findings.append(
                {
                    "kind": "unsafe_path_pattern",
                    "severity": "block",
                    "message": f"path pattern is outside the governed workspace: {path}",
                }
            )

    if approval_policy.get("external_writes"):
        findings.append(
            {
                "kind": "external_writes_require_review",
                "severity": "require-review",
                "message": "external writes approval flag requires human review before execution",
            }
        )

    outcome = outcome_from_findings(findings)
    runtime_action = {"pass": "allow", "require-review": "require-review", "block": "block"}[outcome]
    run_id = str(contract.get("run_id", "unknown-run"))
    generated = generated_at or now_utc()
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
        "generated_at": generated,
        "labels": {"source": "sp-run-readonly-preflight"},
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


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

    preflight = subparsers.add_parser("preflight", help="Project a governed run contract into a read-only preflight receipt.")
    preflight.add_argument("contract_json")
    preflight.add_argument("--generated-at")
    preflight.add_argument("--output")
    preflight.set_defaults(func=command_preflight)

    dossier = subparsers.add_parser("dossier", help="Build a RunDossier from a governed run folder.")
    dossier.add_argument("run_dir")
    dossier.add_argument("--generated-at")
    dossier.add_argument("--output")
    dossier.set_defaults(func=command_dossier)

    validate = subparsers.add_parser("validate-dossier", help="Validate a RunDossier JSON file.")
    validate.add_argument("dossier_json")
    validate.set_defaults(func=command_validate_dossier)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
