#!/usr/bin/env python3
"""Validate SemanticActivationReceipt v0.1 fixtures.

The validator is stdlib-only. It checks the schema, structural fixture shape,
the required activation-input hash binding, the mandatory five semantic edge
classes, admission decision binding, and fail-closed behavior when evidence is
missing or non-replayable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "semantic-activation-receipt.v0.1.schema.json"

REQUIRED_FIELDS = {
    "schemaVersion",
    "recordType",
    "receipt_id",
    "asset_id",
    "ingestion_run_id",
    "activation_bundle_hash",
    "activation_bundle_canonicalization_id",
    "validator_bundle_ref",
    "executor_id",
    "executor_version",
    "graph_snapshot_id",
    "policy_bundle_id",
    "policy_decision_ref",
    "admission_decision",
    "admission_reason_code",
    "quality_snapshot_id",
    "activation_edges",
    "run_artifact_refs",
    "replay_artifact_ref",
    "evidence_status",
    "receipt_hash",
}

REQUIRED_EDGE_TYPES = {
    "declares",
    "depends_on",
    "governed_by",
    "validated_by",
    "replayable_as",
}

ADMISSION_DECISIONS = {
    "admitted",
    "rejected",
    "require-review",
    "fail-closed",
}

FAIL_CLOSED_STATUSES = {
    "missing_evidence",
    "invalid_evidence",
    "non_replayable",
}


class ValidationError(Exception):
    """Raised when a SemanticActivationReceipt fixture is invalid."""


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


def validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    required = set(schema.get("required", []))
    missing = REQUIRED_FIELDS - required
    if missing:
        fail(f"schema missing required receipt fields: {sorted(missing)}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.semantic-activation-receipt.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "SemanticActivationReceipt":
        fail("recordType const mismatch")
    admission_enum = set(props.get("admission_decision", {}).get("enum", []))
    if admission_enum != ADMISSION_DECISIONS:
        fail("admission_decision enum mismatch")


def validate_receipt(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        fail(f"missing required receipt fields: {missing}")

    if record["schemaVersion"] != "agentplane.semantic-activation-receipt.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "SemanticActivationReceipt":
        fail("recordType mismatch")

    for key in REQUIRED_FIELDS - {"activation_edges", "run_artifact_refs"}:
        require_string(record, key)

    if not record["activation_bundle_hash"].startswith("sha256:"):
        fail("activation_bundle_hash must be sha256-bound")
    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")

    run_artifact_refs = record.get("run_artifact_refs")
    if not isinstance(run_artifact_refs, list) or not run_artifact_refs:
        fail("run_artifact_refs must be a non-empty list")
    for index, ref in enumerate(run_artifact_refs):
        if not isinstance(ref, str) or not ref:
            fail(f"run_artifact_refs[{index}] must be a non-empty string")

    validate_activation_edges(record.get("activation_edges"))
    validate_evidence_and_admission(record)
    validate_lineage(record)


def validate_evidence_and_admission(record: dict[str, Any]) -> None:
    evidence_status = record["evidence_status"]
    if evidence_status not in {"complete", "missing_evidence", "invalid_evidence", "non_replayable"}:
        fail(f"invalid evidence_status: {evidence_status}")

    admission_decision = record["admission_decision"]
    if admission_decision not in ADMISSION_DECISIONS:
        fail(f"invalid admission_decision: {admission_decision}")

    if admission_decision == "admitted" and evidence_status != "complete":
        fail("admitted receipts require evidence_status=complete")

    if evidence_status in FAIL_CLOSED_STATUSES and not record.get("fail_closed_reason"):
        fail("fail_closed_reason is required when evidence is missing, invalid, or non-replayable")

    if admission_decision == "fail-closed" and not record.get("fail_closed_reason"):
        fail("fail_closed_reason is required when admission_decision=fail-closed")

    if evidence_status == "complete" and admission_decision != "fail-closed" and record.get("fail_closed_reason"):
        fail("complete non-fail-closed receipts must not carry fail_closed_reason")


def validate_lineage(record: dict[str, Any]) -> None:
    lineage = record.get("lineage", {})
    if lineage:
        if not isinstance(lineage, dict):
            fail("lineage must be an object")
        if lineage.get("stable_across_reassessment") is not True:
            fail("lineage.stable_across_reassessment must be true when lineage is present")
        previous = lineage.get("previous_receipt_refs")
        if not isinstance(previous, list):
            fail("lineage.previous_receipt_refs must be a list")


def validate_activation_edges(edges: Any) -> None:
    if not isinstance(edges, list) or not edges:
        fail("activation_edges must be a non-empty list")

    seen_types: set[str] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            fail(f"activation_edges[{index}] must be an object")
        for key in ("edge_type", "subject_ref", "object_ref", "evidence_ref"):
            value = edge.get(key)
            if not isinstance(value, str) or not value:
                fail(f"activation_edges[{index}].{key}: expected non-empty string")
        edge_type = edge["edge_type"]
        if edge_type not in REQUIRED_EDGE_TYPES:
            fail(f"activation_edges[{index}].edge_type unexpected: {edge_type}")
        seen_types.add(edge_type)

    missing_edges = sorted(REQUIRED_EDGE_TYPES - seen_types)
    if missing_edges:
        fail(f"activation_edges missing mandatory edge types: {missing_edges}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_semantic_activation_receipt.py <fixture.json>", file=sys.stderr)
        return 2

    try:
        schema = load_json(SCHEMA)
        fixture = load_json(Path(argv[1]))
        validate_schema_contract(schema)
        validate_receipt(fixture)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {argv[1]} validates as SemanticActivationReceipt v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
