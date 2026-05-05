#!/usr/bin/env python3
"""Validate AgentPlane evidence receipt binding schema and example.

This bootstrap validator is intentionally stdlib-only. It checks the binding
contract shape, the example fixture, and the core artifact-to-receipt kind map
without adding runtime dependencies to AgentPlane validation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "evidence-receipt-binding.schema.v0.1.json"
EXAMPLE_PATH = ROOT / "examples" / "evidence" / "evidence-receipt-binding.example.json"

EXPECTED_KIND_MAP = {
    "ValidationArtifact": "ValidationReceipt",
    "PromotionArtifact": "PromotionReceipt",
    "RunArtifact": "ExecutionReceipt",
    "ReplayArtifact": "ReplayReceipt",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"expected JSON object in {path.relative_to(ROOT)}")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_schema(schema: dict[str, Any]) -> None:
    props = schema.get("properties", {})
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema must use JSON Schema draft 2020-12")
    require(schema.get("type") == "object", "schema must describe an object")
    require(schema.get("additionalProperties") is False, "schema must be strict")
    require(props.get("kind", {}).get("const") == "AgentPlaneEvidenceReceiptBinding", "schema must declare binding kind const")
    require("artifactKind" in props, "schema must define artifactKind")
    require("receiptKind" in props, "schema must define receiptKind")
    require("fieldMappings" in props, "schema must define fieldMappings")


def validate_example(example: dict[str, Any]) -> None:
    require(example.get("apiVersion") == "agentplane.socioprophet.org/v0.1", "example apiVersion mismatch")
    require(example.get("kind") == "AgentPlaneEvidenceReceiptBinding", "example kind mismatch")
    artifact_kind = example.get("artifactKind")
    receipt_kind = example.get("receiptKind")
    require(artifact_kind in EXPECTED_KIND_MAP, f"unexpected artifactKind: {artifact_kind}")
    require(receipt_kind == EXPECTED_KIND_MAP[artifact_kind], f"{artifact_kind} must map to {EXPECTED_KIND_MAP[artifact_kind]}, got {receipt_kind}")
    require(str(example.get("receiptId", "")).startswith("urn:srcos:receipt:"), "receiptId must use urn:srcos:receipt prefix")
    require(example.get("subjectRef"), "example must include subjectRef")

    standards_refs = example.get("standardsRefs", {})
    require("socioprophet-standards-storage" in standards_refs.get("receiptSpine", ""), "receiptSpine ref must point at standards-storage")
    require("socioprophet-standards-knowledge" in standards_refs.get("knowledgeLifecycle", ""), "knowledgeLifecycle ref must point at standards-knowledge")

    mappings = example.get("fieldMappings")
    require(isinstance(mappings, list) and mappings, "example must include non-empty fieldMappings")
    mapped_receipt_fields = {entry.get("receiptField") for entry in mappings if isinstance(entry, dict)}
    for required_field in {"kind", "subjectRef", "issuedTimeUtc"}:
        require(required_field in mapped_receipt_fields, f"fieldMappings must include receipt field {required_field}")


def main() -> int:
    try:
        schema = load_json(SCHEMA_PATH)
        example = load_json(EXAMPLE_PATH)
        validate_schema(schema)
        validate_example(example)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: validated AgentPlane evidence receipt binding schema and example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
