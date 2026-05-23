#!/usr/bin/env python3
"""Validate BudgetSettlementReceipt v0.1 fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "budget-settlement-receipt.v0.1.schema.json"

REQUIRED_FIELDS = {
    "schemaVersion",
    "recordType",
    "settlement_id",
    "run_id",
    "attempt_id",
    "admission_receipt_ref",
    "settled_at",
    "estimate",
    "actuals",
    "settlement_status",
    "overrun",
    "settlement_provenance",
    "receipt_hash",
}

ESTIMATE_REQUIRED = {
    "projected_cost_usd",
    "remaining_budget_usd",
    "estimate_provenance",
}

ACTUALS_REQUIRED = {
    "tokens_in",
    "tokens_out",
    "tool_calls",
    "wall_clock_ms",
    "cost_usd",
}

OVERRUN_REQUIRED = {
    "over_budget",
    "estimated_cost_usd",
    "actual_cost_usd",
    "status",
}

SETTLEMENT_STATUSES = {
    "settled",
    "overrun",
    "missing_actuals",
    "invalid_actuals",
    "fail-closed",
}

SETTLEMENT_PROVENANCE = {
    "synthetic",
    "measured",
    "estimated",
    "provider-reported",
    "missing",
}


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


def require_object(record: dict[str, Any], key: str) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict):
        fail(f"{key}: expected object")
    return value


def require_nonnegative_number(record: dict[str, Any], key: str) -> float:
    value = record.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{key}: expected number")
    if value < 0:
        fail(f"{key}: expected non-negative number")
    return float(value)


def require_nonnegative_int(record: dict[str, Any], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        fail(f"{key}: expected integer")
    if value < 0:
        fail(f"{key}: expected non-negative integer")
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
    properties = schema.get("properties", {})
    if properties.get("schemaVersion", {}).get("const") != "agentplane.budget-settlement-receipt.v0.1":
        fail("schemaVersion const mismatch")
    if properties.get("recordType", {}).get("const") != "BudgetSettlementReceipt":
        fail("recordType const mismatch")


def validate_receipt(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        fail(f"missing required receipt fields: {missing}")

    if record["schemaVersion"] != "agentplane.budget-settlement-receipt.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "BudgetSettlementReceipt":
        fail("recordType mismatch")

    for key in (
        "settlement_id",
        "run_id",
        "attempt_id",
        "admission_receipt_ref",
        "settled_at",
        "settlement_status",
        "settlement_provenance",
        "receipt_hash",
    ):
        require_string(record, key)

    if not record["admission_receipt_ref"].startswith("attempt-admission-receipt:"):
        fail("admission_receipt_ref must reference an AttemptAdmissionReceipt")
    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")
    if record["settlement_status"] not in SETTLEMENT_STATUSES:
        fail(f"invalid settlement_status: {record['settlement_status']}")
    if record["settlement_provenance"] not in SETTLEMENT_PROVENANCE:
        fail(f"invalid settlement_provenance: {record['settlement_provenance']}")

    estimate = validate_estimate(require_object(record, "estimate"))
    actuals = validate_actuals(require_object(record, "actuals"))
    overrun = validate_overrun(require_object(record, "overrun"))
    validate_consistency(record, estimate, actuals, overrun)


def validate_estimate(estimate: dict[str, Any]) -> dict[str, float]:
    missing = sorted(ESTIMATE_REQUIRED - set(estimate))
    if missing:
        fail(f"estimate missing required fields: {missing}")
    projected = require_nonnegative_number(estimate, "projected_cost_usd")
    remaining = require_nonnegative_number(estimate, "remaining_budget_usd")
    require_string(estimate, "estimate_provenance")
    if "remaining_iterations" in estimate:
        require_nonnegative_int(estimate, "remaining_iterations")
    if "remaining_tokens" in estimate:
        require_nonnegative_int(estimate, "remaining_tokens")
    return {"projected_cost_usd": projected, "remaining_budget_usd": remaining}


def validate_actuals(actuals: dict[str, Any]) -> dict[str, float]:
    missing = sorted(ACTUALS_REQUIRED - set(actuals))
    if missing:
        fail(f"actuals missing required fields: {missing}")
    require_nonnegative_int(actuals, "tokens_in")
    require_nonnegative_int(actuals, "tokens_out")
    require_nonnegative_int(actuals, "tool_calls")
    require_nonnegative_int(actuals, "wall_clock_ms")
    cost = require_nonnegative_number(actuals, "cost_usd")
    return {"cost_usd": cost}


def validate_overrun(overrun: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(OVERRUN_REQUIRED - set(overrun))
    if missing:
        fail(f"overrun missing required fields: {missing}")
    if not isinstance(overrun.get("over_budget"), bool):
        fail("overrun.over_budget must be boolean")
    estimated = require_nonnegative_number(overrun, "estimated_cost_usd")
    actual = require_nonnegative_number(overrun, "actual_cost_usd")
    status = require_string(overrun, "status")
    if status not in {"within_budget", "overrun"}:
        fail(f"invalid overrun.status: {status}")
    return {"over_budget": overrun["over_budget"], "estimated_cost_usd": estimated, "actual_cost_usd": actual, "status": status}


def validate_consistency(record: dict[str, Any], estimate: dict[str, float], actuals: dict[str, float], overrun: dict[str, Any]) -> None:
    settlement_status = record["settlement_status"]
    actual_cost = actuals["cost_usd"]
    projected_cost = estimate["projected_cost_usd"]
    computed_overrun = actual_cost > projected_cost

    if abs(overrun["estimated_cost_usd"] - projected_cost) > 1e-9:
        fail("overrun.estimated_cost_usd must match estimate.projected_cost_usd")
    if abs(overrun["actual_cost_usd"] - actual_cost) > 1e-9:
        fail("overrun.actual_cost_usd must match actuals.cost_usd")
    if overrun["over_budget"] is not computed_overrun:
        fail("overrun.over_budget does not match actuals.cost_usd > estimate.projected_cost_usd")
    if computed_overrun and overrun["status"] != "overrun":
        fail("overrun.status must be overrun when actual cost exceeds projected cost")
    if not computed_overrun and overrun["status"] != "within_budget":
        fail("overrun.status must be within_budget when actual cost is within projection")

    if settlement_status == "settled" and computed_overrun:
        fail("settlement_status=settled cannot hide budget overrun")
    if settlement_status == "overrun" and not computed_overrun:
        fail("settlement_status=overrun requires an actual overrun")

    fail_closed_statuses = {"missing_actuals", "invalid_actuals", "fail-closed"}
    if settlement_status in fail_closed_statuses and not record.get("fail_closed_reason"):
        fail("fail_closed_reason is required for missing/invalid/fail-closed settlement")
    if settlement_status == "missing_actuals" and record["settlement_provenance"] != "missing":
        fail("missing_actuals settlement must use settlement_provenance=missing")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_budget_settlement_receipt.py <fixture.json>", file=sys.stderr)
        return 2
    try:
        schema = load_json(SCHEMA)
        fixture = load_json(Path(argv[1]))
        validate_schema_contract(schema)
        validate_receipt(fixture)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as BudgetSettlementReceipt v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
