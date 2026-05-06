#!/usr/bin/env python3
"""Validate OrgGov work-order evidence binding artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/orggov-workorder-evidence.v0.1.schema.json"
EXAMPLE = ROOT / "examples/orggov/orggov-workorder-evidence.v0.1.example.json"


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


def require_non_empty_string(record: dict[str, Any], key: str) -> None:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")


def require_non_empty_list(record: dict[str, Any], key: str) -> None:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key}: expected non-empty list")
    if not all(isinstance(item, str) and item for item in value):
        fail(f"{key}: expected non-empty string refs")


def validate_binding(record: dict[str, Any]) -> None:
    for key in (
        "workroomRef",
        "workOrderRef",
        "actorRef",
        "roleBindingRef",
        "bundleRef",
        "validationArtifactRef",
        "placementDecisionRef",
        "runArtifactRef",
        "replayArtifactRef",
        "sessionArtifactRef",
    ):
        require_non_empty_string(record, key)

    for key in ("policyDecisionRefs", "outputRefs", "reviewRefs", "outcomeRefs"):
        require_non_empty_list(record, key)

    provenance = record.get("provenance", {})
    if provenance.get("nonSecret") is not True:
        fail("provenance.nonSecret must be true")


def main() -> int:
    try:
        schema = load_json(SCHEMA)
        example = load_json(EXAMPLE)
        validate_schema(schema, example)
        validate_binding(example)
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2

    print("ok: examples/orggov/orggov-workorder-evidence.v0.1.example.json validates")
    print("OK: OrgGov work-order evidence validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
