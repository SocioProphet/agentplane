#!/usr/bin/env python3
"""Build RestoreAdmissionReceipt v0.1 without executing restore actions.

This tool is the functional admission path for governed-runner recovery. It
composes a governed run contract, an OriginalAttemptContext, verifier posture,
halt reason, and budget posture into a validated RestoreAdmissionReceipt.

It does not restore, retry, resume, rollback, mutate files, call providers,
settle budget, or change authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_restore_admission_receipt

EXECUTABLE_ACTIONS = {
    "retry_same_payload",
    "retry_replanned_payload",
    "resume_from_checkpoint",
    "rollback_only",
    "rollback_then_retry",
}
RESTORE_ACTIONS = EXECUTABLE_ACTIONS | {"operator_review_only"}
HALT_REASONS = {
    "budget_exhausted",
    "verifier_failed",
    "policy_denied",
    "runtime_error",
    "operator_halt",
    "timeout",
    "network_denied",
    "side_effect_uncertain",
    "unknown",
}
VERIFIER_STATES = {"passed", "failed", "stale", "missing", "inconclusive"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def stable_hash(record: dict[str, Any]) -> str:
    copy = dict(record)
    copy.pop("receipt_hash", None)
    payload = json.dumps(copy, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def contract_budget(contract: dict[str, Any]) -> dict[str, Any]:
    budget = contract.get("budget", {}) if isinstance(contract.get("budget"), dict) else {}
    return {
        "remaining_budget_usd": float(budget.get("max_usd", 0.0)),
        "remaining_iterations": int(budget.get("max_iterations", 0)),
        "remaining_tokens": int(budget.get("max_tokens", 0)),
        "estimate_provenance": "estimated",
    }


def add_ref(refs: dict[str, str], key: str, value: Any) -> None:
    if isinstance(value, str) and value:
        refs[key] = value


def evidence_refs(original_context: dict[str, Any], context_ref: str, args: argparse.Namespace) -> dict[str, str]:
    refs: dict[str, str] = {"original_attempt_context_ref": context_ref}
    add_ref(refs, "attempt_admission_receipt_ref", args.attempt_admission_receipt_ref or original_context.get("original_admission_ref"))
    add_ref(refs, "verifier_receipt_ref", args.verifier_receipt_ref or original_context.get("original_verification_receipt_ref"))
    add_ref(refs, "runtime_receipt_ref", args.runtime_receipt_ref or original_context.get("original_runtime_receipt_ref"))
    add_ref(refs, "budget_settlement_receipt_ref", args.budget_settlement_receipt_ref)
    add_ref(refs, "run_dossier_ref", args.run_dossier_ref)
    add_ref(refs, "rollback_boundary_ref", args.rollback_boundary_ref)
    add_ref(refs, "operator_assertion_ref", args.operator_assertion_ref)
    return refs


def has_budget_capacity(remaining: dict[str, Any], required: dict[str, Any]) -> bool:
    return (
        remaining["remaining_budget_usd"] >= required["required_budget_usd"]
        and remaining["remaining_iterations"] >= required["required_iterations"]
        and remaining["remaining_tokens"] >= required["required_tokens"]
    )


def restore_admission_policy(
    *,
    requested_action: str,
    halt_reason: str,
    verifier_state: str,
    side_effect_boundary: str,
    original_recovery_posture: str,
    original_retry_posture: str,
    budget_sufficient: bool,
) -> tuple[bool, str, str, list[str], list[str], list[str], str | None, str | None]:
    all_actions = sorted(EXECUTABLE_ACTIONS)
    review_reasons: list[str] = []
    next_options = {"inspect_dossier", "stop"}

    if side_effect_boundary == "confirmed" or original_recovery_posture == "blocked" or original_retry_posture == "do_not_retry":
        return (
            False,
            "deny",
            "blocked",
            [],
            all_actions,
            sorted(next_options | {"rollback", "settle_budget"}),
            "confirmed or blocked recovery posture prevents autonomous restore admission",
            None,
        )

    if requested_action == "operator_review_only":
        review_reasons.append("requested action is operator review only")
    if side_effect_boundary in {"possible", "unknown"}:
        review_reasons.append(f"side_effect_boundary={side_effect_boundary} requires review")
        next_options.add("review_original_attempt")
        next_options.add("rollback")
    if original_recovery_posture == "requires_review" or original_retry_posture == "review_required":
        review_reasons.append("original attempt context requires review")
        next_options.add("review_original_attempt")
    if verifier_state != "passed":
        review_reasons.append(f"verifier_state={verifier_state} prevents autonomous admission")
        next_options.add("refresh_verifier")
    if halt_reason == "unknown":
        review_reasons.append("unknown halt reason requires review")
        next_options.add("review_original_attempt")
    if not budget_sufficient:
        review_reasons.append("required budget exceeds remaining budget")
        next_options.add("settle_budget")

    if review_reasons:
        return (
            False,
            "require-review",
            "requires_review",
            [],
            all_actions,
            sorted(next_options),
            "; ".join(review_reasons),
            None,
        )

    if requested_action not in EXECUTABLE_ACTIONS:
        return (
            False,
            "fail-closed",
            "blocked",
            [],
            all_actions,
            sorted(next_options),
            "requested action is not executable",
            "requested restore action is outside executable recovery actions",
        )

    return (
        True,
        "admit",
        "eligible_for_retry",
        [requested_action],
        sorted(EXECUTABLE_ACTIONS - {requested_action}),
        sorted(next_options | {"retry"}),
        None,
        None,
    )


def build_restore_admission_receipt(
    contract: dict[str, Any],
    original_context: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    run_id = str(contract.get("run_id", "unknown-run"))
    context_ref = str(original_context.get("context_id") or original_context.get("original_attempt_ref") or "missing:original-attempt-context")
    requested_action = str(args.requested_restore_action)
    halt_reason = str(args.halt_reason)
    verifier_state = str(args.verifier_state)
    side_effect_boundary = str(original_context.get("side_effect_boundary", "unknown"))
    original_recovery_posture = str(original_context.get("recovery_policy_posture", "requires_review"))
    original_retry_posture = str(original_context.get("retry_posture", "review_required"))

    remaining = contract_budget(contract)
    if args.remaining_budget_usd is not None:
        remaining["remaining_budget_usd"] = args.remaining_budget_usd
        remaining["estimate_provenance"] = "actual"
    if args.remaining_iterations is not None:
        remaining["remaining_iterations"] = args.remaining_iterations
        remaining["estimate_provenance"] = "actual"
    if args.remaining_tokens is not None:
        remaining["remaining_tokens"] = args.remaining_tokens
        remaining["estimate_provenance"] = "actual"

    required = {
        "required_budget_usd": args.required_budget_usd,
        "required_iterations": args.required_iterations,
        "required_tokens": args.required_tokens,
        "estimate_provenance": "estimated",
    }

    admitted, decision, final_posture, admitted_actions, blocked_actions, next_options, review_reason, fail_closed_reason = restore_admission_policy(
        requested_action=requested_action,
        halt_reason=halt_reason,
        verifier_state=verifier_state,
        side_effect_boundary=side_effect_boundary,
        original_recovery_posture=original_recovery_posture,
        original_retry_posture=original_retry_posture,
        budget_sufficient=has_budget_capacity(remaining, required),
    )

    receipt: dict[str, Any] = {
        "schemaVersion": "agentplane.restore-admission-receipt.v0.1",
        "recordType": "RestoreAdmissionReceipt",
        "receipt_id": f"restore-admission-receipt:{run_id}:001",
        "restore_attempt_id": f"restore-attempt:{run_id}:001",
        "run_id": run_id,
        "governed_run_contract_ref": str(contract.get("contract_id", f"governed-run-contract:{run_id}")),
        "original_attempt_context_ref": context_ref,
        "requested_restore_action": requested_action,
        "halt_reason": halt_reason,
        "verifier_state": verifier_state,
        "budget_remaining": remaining,
        "budget_required": required,
        "side_effect_boundary": side_effect_boundary,
        "recovery_policy_posture": final_posture,
        "admitted": admitted,
        "admission_decision": decision,
        "admitted_actions": admitted_actions,
        "blocked_actions": blocked_actions,
        "operator_next_options": next_options,
        "review_reason": review_reason,
        "fail_closed_reason": fail_closed_reason,
        "evidence_refs": evidence_refs(original_context, context_ref, args),
        "issued_at": args.generated_at or now_utc(),
        "labels": {
            "source": "build_restore_admission_receipt",
            "issue": "SocioProphet/agentplane#206",
        },
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    validate_restore_admission_receipt.validate_schema_contract(
        validate_restore_admission_receipt.load_json(validate_restore_admission_receipt.SCHEMA)
    )
    validate_restore_admission_receipt.validate_receipt(receipt)


def write_receipt(receipt: dict[str, Any], output: str | None) -> None:
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build_restore_admission_receipt.py")
    parser.add_argument("contract_json")
    parser.add_argument("--original-attempt-context", dest="original_attempt_context_json", required=True)
    parser.add_argument("--requested-restore-action", choices=sorted(RESTORE_ACTIONS), required=True)
    parser.add_argument("--halt-reason", choices=sorted(HALT_REASONS), required=True)
    parser.add_argument("--verifier-state", choices=sorted(VERIFIER_STATES), required=True)
    parser.add_argument("--required-budget-usd", type=float, required=True)
    parser.add_argument("--required-iterations", type=int, required=True)
    parser.add_argument("--required-tokens", type=int, required=True)
    parser.add_argument("--remaining-budget-usd", type=float)
    parser.add_argument("--remaining-iterations", type=int)
    parser.add_argument("--remaining-tokens", type=int)
    parser.add_argument("--attempt-admission-receipt-ref")
    parser.add_argument("--budget-settlement-receipt-ref")
    parser.add_argument("--verifier-receipt-ref")
    parser.add_argument("--runtime-receipt-ref")
    parser.add_argument("--run-dossier-ref")
    parser.add_argument("--rollback-boundary-ref")
    parser.add_argument("--operator-assertion-ref")
    parser.add_argument("--generated-at")
    parser.add_argument("--output")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        contract = load_json_object(Path(args.contract_json))
        original_context = load_json_object(Path(args.original_attempt_context_json))
        receipt = build_restore_admission_receipt(contract, original_context, args)
        validate_receipt(receipt)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    write_receipt(receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
