#!/usr/bin/env python3
"""Validate RunDossier v0.1 fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "runs" / "run-dossier.v0.1.schema.json"

REQUIRED = {
    "schemaVersion",
    "recordType",
    "dossier_id",
    "run_id",
    "generated_at",
    "source_run_dir",
    "overall_status",
    "contract_ref",
    "attempt_count",
    "budget_summary",
    "latest_admission",
    "latest_rollback",
    "receipt_refs",
    "missing_receipts",
    "recommended_next_action",
    "dossier_hash",
}

STATUS = {"ready", "blocked", "requires_review", "failed_closed", "incomplete"}


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


def require_number(record: dict[str, Any], key: str) -> float:
    value = record.get(key)
    if not isinstance(value, (int, float)) or value < 0:
        fail(f"{key}: expected non-negative number")
    return float(value)


def require_int(record: dict[str, Any], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or value < 0:
        fail(f"{key}: expected non-negative integer")
    return value


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    required = set(schema.get("required", []))
    missing = sorted(REQUIRED - required)
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.run-dossier.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "RunDossier":
        fail("recordType const mismatch")


def validate_dossier(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"RunDossier missing required fields: {missing}")
    if record["schemaVersion"] != "agentplane.run-dossier.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "RunDossier":
        fail("recordType mismatch")
    for key in (
        "dossier_id",
        "run_id",
        "generated_at",
        "source_run_dir",
        "overall_status",
        "contract_ref",
        "recommended_next_action",
        "dossier_hash",
    ):
        require_string(record, key)
    if record["overall_status"] not in STATUS:
        fail(f"unknown overall_status: {record['overall_status']}")
    if not record["dossier_hash"].startswith("sha256:"):
        fail("dossier_hash must be sha256-bound")
    require_int(record, "attempt_count")
    validate_budget(record.get("budget_summary"))
    validate_latest_admission(record.get("latest_admission"))
    validate_latest_rollback(record.get("latest_rollback"))
    validate_string_list(record, "receipt_refs", allow_empty=False)
    validate_string_list(record, "missing_receipts", allow_empty=True)
    if record["overall_status"] == "ready" and record["missing_receipts"]:
        fail("ready dossiers cannot have missing receipts")
    if record["overall_status"] == "incomplete" and not record["missing_receipts"]:
        fail("incomplete dossiers must identify missing receipts")


def validate_budget(value: Any) -> None:
    if not isinstance(value, dict):
        fail("budget_summary must be an object")
    for key in ("projected_cost_usd", "remaining_budget_usd"):
        require_number(value, key)
    for key in ("remaining_iterations", "remaining_tokens"):
        require_int(value, key)


def validate_latest_admission(value: Any) -> None:
    if not isinstance(value, dict):
        fail("latest_admission must be an object")
    for key in ("receipt_ref", "admission_decision", "reason_code", "runtime_action", "authority_decision"):
        require_string(value, key)
    if not isinstance(value.get("admitted"), bool):
        fail("latest_admission.admitted must be boolean")


def validate_latest_rollback(value: Any) -> None:
    if not isinstance(value, dict):
        fail("latest_rollback must be an object")
    for key in ("boundary_ref", "result_ref", "status"):
        require_string(value, key)


def validate_string_list(record: dict[str, Any], key: str, *, allow_empty: bool) -> None:
    value = record.get(key)
    if not isinstance(value, list):
        fail(f"{key}: expected list")
    if not allow_empty and not value:
        fail(f"{key}: expected non-empty list")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            fail(f"{key}[{index}]: expected non-empty string")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_run_dossier.py <dossier.json>", file=sys.stderr)
        return 2
    try:
        validate_schema(load_json(SCHEMA))
        validate_dossier(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as RunDossier v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
