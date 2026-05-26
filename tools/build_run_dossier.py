#!/usr/bin/env python3
"""Build a RunDossier from a governed run evidence folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ATTEMPT_FILES = (
    "attempt-admission-receipt.json",
    "runtime-attempt-receipt.json",
    "verification-result.json",
    "rollback-boundary.json",
    "rollback-result.json",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not a JSON object: {path}")
    return data


def hash_record(record: dict[str, Any]) -> str:
    copy = dict(record)
    copy.pop("dossier_hash", None)
    encoded = json.dumps(copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def ref(record: dict[str, Any] | None, fallback: str) -> str:
    if not record:
        return fallback
    for key in ("receipt_id", "boundary_id", "result_id", "verification_id", "run_id"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return fallback


def latest_attempt(run_dir: Path) -> Path | None:
    attempts_root = run_dir / "attempts"
    if not attempts_root.exists():
        return None
    attempts = sorted(path for path in attempts_root.iterdir() if path.is_dir())
    return attempts[-1] if attempts else None


def missing_items(run_dir: Path, attempt_dir: Path | None) -> list[str]:
    missing: list[str] = []
    if not (run_dir / "governed-run-contract.json").exists():
        missing.append("governed-run-contract.json")
    if attempt_dir is None:
        missing.append("attempts/latest")
        return missing
    for filename in ATTEMPT_FILES:
        if not (attempt_dir / filename).exists():
            missing.append(f"attempts/{attempt_dir.name}/{filename}")
    return missing


def status_from(admission: dict[str, Any] | None, missing: list[str]) -> str:
    if missing or not admission:
        return "incomplete"
    decision = admission.get("admission_decision")
    if decision == "fail-closed":
        return "failed_closed"
    if decision == "require-review":
        return "requires_review"
    if admission.get("admitted") is True and admission.get("runtime_action") in {"allow", "warn"}:
        return "ready"
    return "blocked"


def next_action(status: str) -> str:
    table = {
        "ready": "continue",
        "blocked": "inspect_blocking_receipts",
        "requires_review": "route_to_review",
        "failed_closed": "repair_evidence",
        "incomplete": "collect_missing_receipts",
    }
    return table[status]


def restore_admission_panel(restore_admission: dict[str, Any] | None) -> dict[str, Any] | None:
    if restore_admission is None:
        return None
    return {
        "receipt_ref": ref(restore_admission, "missing:restore-admission-receipt"),
        "admitted": bool(restore_admission.get("admitted", False)),
        "admission_decision": str(restore_admission.get("admission_decision", "missing")),
        "requested_restore_action": str(restore_admission.get("requested_restore_action", "missing")),
        "halt_reason": str(restore_admission.get("halt_reason", "missing")),
        "verifier_state": str(restore_admission.get("verifier_state", "missing")),
        "side_effect_boundary": str(restore_admission.get("side_effect_boundary", "missing")),
        "recovery_policy_posture": str(restore_admission.get("recovery_policy_posture", "missing")),
        "budget_remaining": restore_admission.get("budget_remaining", {}),
        "admitted_actions": restore_admission.get("admitted_actions", []),
        "blocked_actions": restore_admission.get("blocked_actions", []),
        "operator_next_options": restore_admission.get("operator_next_options", []),
        "review_reason": restore_admission.get("review_reason"),
        "fail_closed_reason": restore_admission.get("fail_closed_reason"),
    }


def build(run_dir: Path, generated_at: str | None = None) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    contract = load_object(run_dir / "governed-run-contract.json")
    attempt_dir = latest_attempt(run_dir)
    missing = missing_items(run_dir, attempt_dir)

    admission = load_object(attempt_dir / "attempt-admission-receipt.json") if attempt_dir else None
    runtime = load_object(attempt_dir / "runtime-attempt-receipt.json") if attempt_dir else None
    verification = load_object(attempt_dir / "verification-result.json") if attempt_dir else None
    boundary = load_object(attempt_dir / "rollback-boundary.json") if attempt_dir else None
    result = load_object(attempt_dir / "rollback-result.json") if attempt_dir else None
    restore_admission = load_object(attempt_dir / "restore-admission-receipt.json") if attempt_dir else None

    run_id = str((contract or {}).get("run_id") or (admission or {}).get("run_id") or "unknown-run")
    status = status_from(admission, missing)
    budget = (admission or {}).get("budget_estimate", {})
    attempts_root = run_dir / "attempts"
    attempt_count = len([p for p in attempts_root.iterdir() if p.is_dir()]) if attempts_root.exists() else 0

    receipt_refs = [
        ref(contract, f"governed-run-contract:{run_id}"),
        ref(admission, "missing:attempt-admission-receipt"),
        ref(runtime, "missing:runtime-attempt-receipt"),
        ref(verification, "missing:verification-result"),
        ref(boundary, "missing:rollback-boundary"),
        ref(result, "missing:rollback-result"),
    ]
    if restore_admission is not None:
        receipt_refs.append(ref(restore_admission, "missing:restore-admission-receipt"))

    dossier: dict[str, Any] = {
        "schemaVersion": "agentplane.run-dossier.v0.1",
        "recordType": "RunDossier",
        "dossier_id": f"run-dossier:{run_id}",
        "run_id": run_id,
        "generated_at": generated_at or utc_now(),
        "source_run_dir": str(run_dir),
        "overall_status": status,
        "contract_ref": ref(contract, f"governed-run-contract:{run_id}"),
        "attempt_count": attempt_count,
        "budget_summary": {
            "projected_cost_usd": budget.get("projected_cost_usd", 0),
            "remaining_budget_usd": budget.get("remaining_budget_usd", 0),
            "remaining_iterations": budget.get("remaining_iterations", 0),
            "remaining_tokens": budget.get("remaining_tokens", 0),
        },
        "latest_admission": {
            "receipt_ref": ref(admission, "missing:attempt-admission-receipt"),
            "admitted": bool((admission or {}).get("admitted", False)),
            "admission_decision": str((admission or {}).get("admission_decision", "missing")),
            "reason_code": str((admission or {}).get("reason_code", "missing")),
            "runtime_action": str((admission or {}).get("runtime_action", "missing")),
            "authority_decision": str((admission or {}).get("authority_decision", "missing")),
        },
        "latest_rollback": {
            "boundary_ref": ref(boundary, "missing:rollback-boundary"),
            "result_ref": ref(result, "missing:rollback-result"),
            "status": str((result or {}).get("status", "missing")),
        },
        "receipt_refs": receipt_refs,
        "missing_receipts": missing,
        "recommended_next_action": next_action(status),
        "labels": {"source": "receipts"},
    }
    restore_panel = restore_admission_panel(restore_admission)
    if restore_panel is not None:
        dossier["latest_restore_admission"] = restore_panel
    dossier["dossier_hash"] = hash_record(dossier)
    return dossier


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--generated-at")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        dossier = build(Path(args.run_dir), args.generated_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(dossier, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
