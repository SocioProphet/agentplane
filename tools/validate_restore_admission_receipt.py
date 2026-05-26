#!/usr/bin/env python3
"""Validate RestoreAdmissionReceipt v0.1 fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "restore-admission-receipt.v0.1.schema.json"

REQUIRED_FIELDS = {
    "schemaVersion",
    "recordType",
    "receipt_id",
    "restore_attempt_id",
    "run_id",
    "governed_run_contract_ref",
    "original_attempt_context_ref",
    "requested_restore_action",
    "halt_reason",
    "verifier_state",
    "budget_remaining",
    "budget_required",
    "side_effect_boundary",
    "recovery_policy_posture",
    "admitted",
    "admission_decision",
    "admitted_actions",
    "blocked_actions",
    "operator_next_options",
    "evidence_refs",
    "issued_at",
    "receipt_hash",
}

RESTORE_ACTIONS = {
    "retry_same_payload",
    "retry_replanned_payload",
    "resume_from_checkpoint",
    "rollback_only",
    "rollback_then_retry",
    "operator_review_only",
}
ADMISSIBLE_ACTIONS = RESTORE_ACTIONS - {"operator_review_only"}
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
SIDE_EFFECT_BOUNDARIES = {"none", "possible", "confirmed", "unknown"}
RECOVERY_POSTURES = {"eligible_for_retry", "requires_review", "blocked"}
ADMISSION_DECISIONS = {"admit", "require-review", "deny", "fail-closed"}
NEXT_OPTIONS = {
    "retry",
    "review_original_attempt",
    "inspect_dossier",
    "rollback",
    "settle_budget",
    "refresh_verifier",
    "stop",
}
ESTIMATE_PROVENANCE = {"actual", "estimated", "unavailable"}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)}: expected JSON object")
    return payload


def require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def require_bool(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        fail(f"{key}: expected boolean")
    return value


def require_string_set(record: dict[str, Any], key: str, allowed: set[str], *, min_items: int = 0) -> set[str]:
    value = record.get(key)
    if not isinstance(value, list):
        fail(f"{key}: expected array")
    if len(value) < min_items:
        fail(f"{key}: expected at least {min_items} item(s)")
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str) or not item:
            fail(f"{key}: expected non-empty string entries")
        if item not in allowed:
            fail(f"{key}: invalid entry {item}")
        if item in seen:
            fail(f"{key}: duplicate entry {item}")
        seen.add(item)
    return seen


def validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED_FIELDS - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.restore-admission-receipt.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "RestoreAdmissionReceipt":
        fail("recordType const mismatch")


def validate_budget_remaining(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail("budget_remaining: expected object")
    required = {"remaining_budget_usd", "remaining_iterations", "remaining_tokens", "estimate_provenance"}
    missing = sorted(required - set(value))
    if missing:
        fail(f"budget_remaining missing required fields: {missing}")
    remaining_budget = value.get("remaining_budget_usd")
    remaining_iterations = value.get("remaining_iterations")
    remaining_tokens = value.get("remaining_tokens")
    provenance = value.get("estimate_provenance")
    if not isinstance(remaining_budget, (int, float)) or remaining_budget < 0:
        fail("budget_remaining.remaining_budget_usd must be >= 0")
    if not isinstance(remaining_iterations, int) or remaining_iterations < 0:
        fail("budget_remaining.remaining_iterations must be >= 0")
    if not isinstance(remaining_tokens, int) or remaining_tokens < 0:
        fail("budget_remaining.remaining_tokens must be >= 0")
    if provenance not in ESTIMATE_PROVENANCE:
        fail(f"invalid budget_remaining.estimate_provenance: {provenance}")
    return value


def validate_budget_required(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail("budget_required: expected object")
    required = {"required_budget_usd", "required_iterations", "required_tokens", "estimate_provenance"}
    missing = sorted(required - set(value))
    if missing:
        fail(f"budget_required missing required fields: {missing}")
    required_budget = value.get("required_budget_usd")
    required_iterations = value.get("required_iterations")
    required_tokens = value.get("required_tokens")
    provenance = value.get("estimate_provenance")
    if not isinstance(required_budget, (int, float)) or required_budget < 0:
        fail("budget_required.required_budget_usd must be >= 0")
    if not isinstance(required_iterations, int) or required_iterations < 0:
        fail("budget_required.required_iterations must be >= 0")
    if not isinstance(required_tokens, int) or required_tokens < 0:
        fail("budget_required.required_tokens must be >= 0")
    if provenance not in ESTIMATE_PROVENANCE:
        fail(f"invalid budget_required.estimate_provenance: {provenance}")
    return value


def validate_evidence_refs(record: dict[str, Any]) -> None:
    refs = record.get("evidence_refs")
    if not isinstance(refs, dict):
        fail("evidence_refs: expected object")
    context_ref = require_string(record, "original_attempt_context_ref")
    nested_context_ref = refs.get("original_attempt_context_ref")
    if not isinstance(nested_context_ref, str) or not nested_context_ref:
        fail("evidence_refs.original_attempt_context_ref is required")
    if nested_context_ref != context_ref:
        fail("evidence_refs.original_attempt_context_ref must match original_attempt_context_ref")
    for key, value in refs.items():
        if not isinstance(value, str) or not value:
            fail(f"evidence_refs.{key}: expected non-empty string")


def validate_receipt(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        fail(f"missing required fields: {missing}")

    if record["schemaVersion"] != "agentplane.restore-admission-receipt.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "RestoreAdmissionReceipt":
        fail("recordType mismatch")

    for key in (
        "receipt_id",
        "restore_attempt_id",
        "run_id",
        "governed_run_contract_ref",
        "original_attempt_context_ref",
        "requested_restore_action",
        "halt_reason",
        "verifier_state",
        "side_effect_boundary",
        "recovery_policy_posture",
        "admission_decision",
        "issued_at",
        "receipt_hash",
    ):
        require_string(record, key)

    admitted = require_bool(record, "admitted")
    action = record["requested_restore_action"]
    halt_reason = record["halt_reason"]
    verifier_state = record["verifier_state"]
    boundary = record["side_effect_boundary"]
    posture = record["recovery_policy_posture"]
    decision = record["admission_decision"]

    if action not in RESTORE_ACTIONS:
        fail(f"invalid requested_restore_action: {action}")
    if halt_reason not in HALT_REASONS:
        fail(f"invalid halt_reason: {halt_reason}")
    if verifier_state not in VERIFIER_STATES:
        fail(f"invalid verifier_state: {verifier_state}")
    if boundary not in SIDE_EFFECT_BOUNDARIES:
        fail(f"invalid side_effect_boundary: {boundary}")
    if posture not in RECOVERY_POSTURES:
        fail(f"invalid recovery_policy_posture: {posture}")
    if decision not in ADMISSION_DECISIONS:
        fail(f"invalid admission_decision: {decision}")
    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")

    admitted_actions = require_string_set(record, "admitted_actions", ADMISSIBLE_ACTIONS)
    blocked_actions = require_string_set(record, "blocked_actions", ADMISSIBLE_ACTIONS)
    require_string_set(record, "operator_next_options", NEXT_OPTIONS, min_items=1)

    overlap = admitted_actions & blocked_actions
    if overlap:
        fail(f"actions cannot be both admitted and blocked: {sorted(overlap)}")

    remaining = validate_budget_remaining(record["budget_remaining"])
    required = validate_budget_required(record["budget_required"])
    validate_evidence_refs(record)

    budget_sufficient = (
        remaining["remaining_budget_usd"] >= required["required_budget_usd"]
        and remaining["remaining_iterations"] >= required["required_iterations"]
        and remaining["remaining_tokens"] >= required["required_tokens"]
    )

    if admitted and decision != "admit":
        fail("admitted=true requires admission_decision=admit")
    if decision == "admit" and not admitted:
        fail("admission_decision=admit requires admitted=true")
    if decision in {"require-review", "deny", "fail-closed"} and admitted:
        fail(f"{decision} cannot autonomously admit a restore attempt")
    if not admitted and admitted_actions:
        fail("non-admitted restore receipts must not expose admitted_actions")
    if admitted:
        if action == "operator_review_only":
            fail("operator_review_only cannot be autonomously admitted")
        if action not in admitted_actions:
            fail("admitted restore receipt must include requested action in admitted_actions")

    if not budget_sufficient and admitted:
        fail("restore attempt cannot be admitted when required budget exceeds remaining budget")

    if verifier_state != "passed" and admitted:
        fail(f"restore attempt cannot be admitted when verifier_state={verifier_state}")
    if verifier_state in {"stale", "missing", "inconclusive"} and decision == "admit":
        fail(f"verifier_state={verifier_state} must not produce admission")
    if verifier_state == "failed" and decision == "admit":
        fail("verifier_state=failed must not produce admission")

    if boundary in {"possible", "unknown"}:
        if decision != "require-review":
            fail(f"side_effect_boundary={boundary} must require review")
        if record.get("review_reason") is None:
            fail(f"side_effect_boundary={boundary} requires review_reason")
    if boundary == "confirmed":
        if decision not in {"deny", "fail-closed"}:
            fail("confirmed side effects must deny or fail closed")
        if record.get("review_reason") is None:
            fail("confirmed side effects require review_reason")

    if posture == "eligible_for_retry" and boundary != "none":
        fail("eligible_for_retry requires side_effect_boundary=none")
    if posture == "eligible_for_retry" and decision != "admit":
        fail("eligible_for_retry must produce admission")
    if posture == "requires_review" and decision != "require-review":
        fail("requires_review must produce admission_decision=require-review")
    if posture == "blocked" and decision not in {"deny", "fail-closed"}:
        fail("blocked recovery posture must deny or fail closed")
    if posture != "eligible_for_retry" and admitted:
        fail("only eligible_for_retry posture may admit restore execution")

    if halt_reason == "unknown":
        if decision == "admit":
            fail("unknown halt reason cannot admit restore execution")
        if record.get("review_reason") is None:
            fail("unknown halt reason requires review_reason")

    if decision == "require-review" and not record.get("review_reason"):
        fail("require-review requires review_reason")
    if decision == "deny" and not record.get("review_reason"):
        fail("deny requires review_reason")
    if decision == "fail-closed" and not record.get("fail_closed_reason"):
        fail("fail-closed requires fail_closed_reason")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_restore_admission_receipt.py <fixture.json>", file=sys.stderr)
        return 2

    try:
        validate_schema_contract(load_json(SCHEMA))
        validate_receipt(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {argv[1]} validates as RestoreAdmissionReceipt v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
