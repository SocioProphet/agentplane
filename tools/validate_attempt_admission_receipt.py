#!/usr/bin/env python3
"""Validate AttemptAdmissionReceipt v0.1 fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "attempt-admission-receipt.v0.1.schema.json"

REQUIRED_FIELDS = {
    "schemaVersion",
    "recordType",
    "receipt_id",
    "attempt_id",
    "run_id",
    "governed_run_contract_ref",
    "admitted",
    "admission_decision",
    "reason_code",
    "safety_preflight_ref",
    "safety_preflight_outcome",
    "authority_state_ref",
    "authority_decision",
    "trustops_runtime_action_ref",
    "runtime_action",
    "budget_estimate",
    "issued_at",
    "receipt_hash",
}

REQUIRED_BUDGET_FIELDS = {
    "projected_cost_usd",
    "remaining_budget_usd",
    "remaining_iterations",
    "remaining_tokens",
    "estimate_provenance",
}

ADMISSION_DECISIONS = {"admit", "reject", "require-review", "fail-closed"}
TRUSTOPS_OUTCOMES = {"pass", "warn", "require-review", "quarantine", "block", "rollback", "revoke"}
AUTHORITY_DECISIONS = {"unchanged", "reduced", "suspended", "revoked"}
RUNTIME_ACTIONS = {"allow", "warn", "require-review", "quarantine", "block", "rollback", "revoke"}
ESTIMATE_PROVENANCE = {"actual", "estimated", "unavailable"}
BLOCKING_RUNTIME_ACTIONS = {"quarantine", "block", "rollback", "revoke"}
BLOCKING_TRUSTOPS_OUTCOMES = {"quarantine", "block", "rollback", "revoke"}
BLOCKING_AUTHORITY_DECISIONS = {"suspended", "revoked"}


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


def validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    required = set(schema.get("required", []))
    missing = sorted(REQUIRED_FIELDS - required)
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.attempt-admission-receipt.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "AttemptAdmissionReceipt":
        fail("recordType const mismatch")


def validate_receipt(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        fail(f"missing required fields: {missing}")

    if record["schemaVersion"] != "agentplane.attempt-admission-receipt.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "AttemptAdmissionReceipt":
        fail("recordType mismatch")

    for key in (
        "receipt_id",
        "attempt_id",
        "run_id",
        "governed_run_contract_ref",
        "admission_decision",
        "reason_code",
        "safety_preflight_ref",
        "safety_preflight_outcome",
        "authority_state_ref",
        "authority_decision",
        "trustops_runtime_action_ref",
        "runtime_action",
        "issued_at",
        "receipt_hash",
    ):
        require_string(record, key)
    admitted = require_bool(record, "admitted")

    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")

    admission_decision = record["admission_decision"]
    safety_outcome = record["safety_preflight_outcome"]
    authority_decision = record["authority_decision"]
    runtime_action = record["runtime_action"]

    if admission_decision not in ADMISSION_DECISIONS:
        fail(f"invalid admission_decision: {admission_decision}")
    if safety_outcome not in TRUSTOPS_OUTCOMES:
        fail(f"invalid safety_preflight_outcome: {safety_outcome}")
    if authority_decision not in AUTHORITY_DECISIONS:
        fail(f"invalid authority_decision: {authority_decision}")
    if runtime_action not in RUNTIME_ACTIONS:
        fail(f"invalid runtime_action: {runtime_action}")

    budget = validate_budget(record.get("budget_estimate"))

    if admitted and admission_decision != "admit":
        fail("admitted=true requires admission_decision=admit")
    if admission_decision == "admit" and not admitted:
        fail("admission_decision=admit requires admitted=true")
    if not admitted and admission_decision == "admit":
        fail("admitted=false cannot carry admission_decision=admit")

    if admission_decision == "fail-closed" and not record.get("fail_closed_reason"):
        fail("fail_closed_reason is required when admission_decision=fail-closed")

    if budget["projected_cost_usd"] > budget["remaining_budget_usd"] and admitted:
        fail("attempt cannot be admitted when projected cost exceeds remaining budget")
    if budget["remaining_iterations"] <= 0 and admitted:
        fail("attempt cannot be admitted with no remaining iterations")
    if budget["remaining_tokens"] <= 0 and admitted:
        fail("attempt cannot be admitted with no remaining tokens")

    if safety_outcome in BLOCKING_TRUSTOPS_OUTCOMES and admitted:
        fail(f"attempt cannot be admitted when safety_preflight_outcome={safety_outcome}")
    if safety_outcome == "require-review" and admission_decision != "require-review":
        fail("safety require-review must produce admission_decision=require-review")

    if authority_decision in BLOCKING_AUTHORITY_DECISIONS and admitted:
        fail(f"attempt cannot be admitted when authority_decision={authority_decision}")

    if runtime_action in BLOCKING_RUNTIME_ACTIONS and admitted:
        fail(f"attempt cannot be admitted when runtime_action={runtime_action}")
    if runtime_action == "require-review" and admission_decision != "require-review":
        fail("runtime_action=require-review must produce admission_decision=require-review")

    if admission_decision == "require-review" and admitted:
        fail("require-review admission decisions are not autonomous admissions")
    if admission_decision in {"reject", "fail-closed"} and admitted:
        fail(f"{admission_decision} cannot admit an attempt")


def validate_budget(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail("budget_estimate: expected object")
    missing = sorted(REQUIRED_BUDGET_FIELDS - set(value))
    if missing:
        fail(f"budget_estimate missing required fields: {missing}")
    projected = value.get("projected_cost_usd")
    remaining_budget = value.get("remaining_budget_usd")
    remaining_iterations = value.get("remaining_iterations")
    remaining_tokens = value.get("remaining_tokens")
    provenance = value.get("estimate_provenance")
    if not isinstance(projected, (int, float)) or projected < 0:
        fail("budget_estimate.projected_cost_usd must be >= 0")
    if not isinstance(remaining_budget, (int, float)) or remaining_budget < 0:
        fail("budget_estimate.remaining_budget_usd must be >= 0")
    if not isinstance(remaining_iterations, int) or remaining_iterations < 0:
        fail("budget_estimate.remaining_iterations must be >= 0")
    if not isinstance(remaining_tokens, int) or remaining_tokens < 0:
        fail("budget_estimate.remaining_tokens must be >= 0")
    if provenance not in ESTIMATE_PROVENANCE:
        fail(f"invalid budget_estimate.estimate_provenance: {provenance}")
    return value


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_attempt_admission_receipt.py <fixture.json>", file=sys.stderr)
        return 2

    try:
        validate_schema_contract(load_json(SCHEMA))
        validate_receipt(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {argv[1]} validates as AttemptAdmissionReceipt v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
