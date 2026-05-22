#!/usr/bin/env python3
"""Validate PreflightReceipt v0.1 fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "preflight-receipt.v0.1.schema.json"

REQUIRED = {
    "schemaVersion",
    "recordType",
    "receipt_id",
    "run_id",
    "governed_run_contract_ref",
    "mode",
    "authoritative_safety_owner",
    "outcome",
    "runtime_action",
    "safety_preflight_input",
    "findings",
    "generated_at",
    "receipt_hash",
}

OUTCOME_ACTION = {
    "pass": "allow",
    "require-review": "require-review",
    "block": "block",
}

FINDING_SEVERITY = {"info", "require-review", "block"}


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


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")


def validate_receipt(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"PreflightReceipt missing required fields: {missing}")
    if record["schemaVersion"] != "agentplane.preflight-receipt.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "PreflightReceipt":
        fail("recordType mismatch")
    for key in (
        "receipt_id",
        "run_id",
        "governed_run_contract_ref",
        "mode",
        "authoritative_safety_owner",
        "outcome",
        "runtime_action",
        "generated_at",
        "receipt_hash",
    ):
        require_string(record, key)
    if record["mode"] != "readonly_projection":
        fail("mode must be readonly_projection")
    if record["authoritative_safety_owner"] != "SocioProphet/guardrail-fabric":
        fail("authoritative_safety_owner must be SocioProphet/guardrail-fabric")
    outcome = record["outcome"]
    if outcome not in OUTCOME_ACTION:
        fail(f"invalid outcome: {outcome}")
    if record["runtime_action"] != OUTCOME_ACTION[outcome]:
        fail("runtime_action must match outcome")
    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")
    if not isinstance(record.get("safety_preflight_input"), dict):
        fail("safety_preflight_input must be an object")
    findings = record.get("findings")
    if not isinstance(findings, list):
        fail("findings must be a list")
    severities = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            fail(f"findings[{index}] must be an object")
        for key in ("kind", "severity", "message"):
            if not isinstance(finding.get(key), str) or not finding[key]:
                fail(f"findings[{index}].{key}: expected non-empty string")
        if finding["severity"] not in FINDING_SEVERITY:
            fail(f"findings[{index}].severity invalid: {finding['severity']}")
        severities.add(finding["severity"])
    if outcome == "pass" and findings:
        fail("pass preflight receipts must not carry findings")
    if outcome == "block" and "block" not in severities:
        fail("block preflight receipts require a block finding")
    if outcome == "require-review" and "require-review" not in severities:
        fail("require-review preflight receipts require a review finding")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_preflight_receipt.py <preflight-receipt.json>", file=sys.stderr)
        return 2
    try:
        validate_schema(load_json(SCHEMA))
        validate_receipt(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as PreflightReceipt v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
