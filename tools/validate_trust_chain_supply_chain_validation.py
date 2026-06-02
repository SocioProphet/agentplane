#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "trust-chain" / "supply-chain-validation-artifact.v0.1.schema.json"
VALID_FIXTURE = ROOT / "tests" / "fixtures" / "trust-chain" / "supply-chain-validation.valid.json"
BLOCKED_FIXTURE = ROOT / "tests" / "fixtures" / "trust-chain" / "supply-chain-validation.blocked.json"

REQUIRED_PRODUCTION_REFS = {
    "sbom_ref",
    "vex_ref",
    "lockfile_ref",
    "signature_ref",
    "scan_record_ref",
    "promotion_evidence_ref",
    "rollback_evidence_ref",
}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(value: Any, expected: str) -> bool:
    actual = json_type_name(value)
    if expected == "number":
        return actual in {"integer", "number"}
    return actual == expected


def validate_schema(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        fail(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        fail(f"{path}: {value!r} not in enum {schema['enum']!r}")
    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected_types):
            fail(f"{path}: expected type {expected_types!r}, got {json_type_name(value)!r}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                fail(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                fail(f"{path}: unexpected properties {extra!r}")
        additional = schema.get("additionalProperties")
        for key, item in value.items():
            child_schema = properties.get(key)
            if child_schema is None and isinstance(additional, dict):
                child_schema = additional
            if child_schema is not None:
                validate_schema(child_schema, item, f"{path}.{key}")
    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                validate_schema(item_schema, item, f"{path}[{index}]")


def validate_common(record: dict[str, Any], path: Path) -> None:
    if not str(record.get("runtime_asset_ref", "")).startswith("runtime-asset://"):
        fail(f"{path}: runtime_asset_ref must be runtime-asset://")
    if record.get("scope", {}).get("environment") == "production" and record.get("scope", {}).get("risk_tier") == "regulated_enterprise":
        if record.get("decision") == "validated":
            refs = record.get("evidence_refs", {})
            missing = sorted(key for key in REQUIRED_PRODUCTION_REFS if not refs.get(key))
            if missing:
                fail(f"{path}: validated production record missing refs: {missing}")
            for ref_key in ("policy_decision_ref", "guardrail_decision_ref", "validation_artifact_ref", "replay_artifact_ref", "runtime_receipt_ref"):
                if not record.get(ref_key):
                    fail(f"{path}: validated production record missing {ref_key}")


def validate_valid(record: dict[str, Any], path: Path) -> None:
    validate_common(record, path)
    if record.get("decision") != "validated":
        fail(f"{path}: valid fixture must have decision=validated")
    effects = record.get("effects", {})
    if effects.get("execution_allowed") is not True or effects.get("promotion_allowed") is not True:
        fail(f"{path}: valid fixture must allow execution and promotion")
    if effects.get("repair_required") is not False or effects.get("human_review_required") is not False:
        fail(f"{path}: valid fixture must not require repair or review")


def validate_blocked(record: dict[str, Any], path: Path) -> None:
    validate_common(record, path)
    if record.get("decision") != "blocked":
        fail(f"{path}: blocked fixture must have decision=blocked")
    effects = record.get("effects", {})
    if effects.get("execution_allowed") is not False or effects.get("promotion_allowed") is not False:
        fail(f"{path}: blocked fixture must deny execution and promotion")
    if effects.get("repair_required") is not True or effects.get("human_review_required") is not True:
        fail(f"{path}: blocked fixture must require repair and human review")
    remediation = record.get("remediation", [])
    if not isinstance(remediation, list) or len(remediation) < 1:
        fail(f"{path}: blocked fixture requires remediation")
    for item in remediation:
        if item.get("required_before_execution") is not True:
            fail(f"{path}: remediation must be required before execution")
        if not item.get("authority"):
            fail(f"{path}: remediation requires authority")


def main() -> int:
    try:
        schema = load_json(SCHEMA)
        valid = load_json(VALID_FIXTURE)
        blocked = load_json(BLOCKED_FIXTURE)
        validate_schema(schema, valid)
        validate_schema(schema, blocked)
        validate_valid(valid, VALID_FIXTURE)
        validate_blocked(blocked, BLOCKED_FIXTURE)
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2
    print("OK: Trust Chain supply-chain validation artifacts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
