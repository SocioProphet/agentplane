#!/usr/bin/env python3
"""Validate the semantic activation context-divergence proof fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import validate_semantic_activation_receipt

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHAIN = ROOT / "tests" / "fixtures" / "receipts" / "semantic-activation-context-divergence.chain.json"
REQUIRED_CHAIN_FIELDS = {
    "schemaVersion",
    "recordType",
    "proof_id",
    "issue_ref",
    "activation_bundle_hash",
    "admitted_receipt_path",
    "fail_closed_receipt_path",
    "required_invariant",
    "expected_admitted_decision",
    "expected_fail_closed_decision",
    "required_context_differences",
    "operator_boundary",
}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        fail(f"{path}: expected JSON object")
    return payload


def resolve_repo_path(value: str) -> Path:
    path = ROOT / value
    if not path.resolve().is_relative_to(ROOT.resolve()):
        fail(f"path escapes repository root: {value}")
    return path


def require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def require_list(record: dict[str, Any], key: str) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key}: expected non-empty list")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            fail(f"{key}[{index}]: expected non-empty string")
    return value


def validate_chain(chain: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_CHAIN_FIELDS - set(chain))
    if missing:
        fail(f"chain missing required fields: {missing}")
    if chain["schemaVersion"] != "agentplane.semantic-activation-context-divergence.v0.1":
        fail("chain schemaVersion mismatch")
    if chain["recordType"] != "SemanticActivationContextDivergenceProof":
        fail("chain recordType mismatch")
    activation_hash = require_string(chain, "activation_bundle_hash")
    if not activation_hash.startswith("sha256:"):
        fail("chain activation_bundle_hash must be sha256-bound")

    admitted = load_receipt(require_string(chain, "admitted_receipt_path"))
    failed = load_receipt(require_string(chain, "fail_closed_receipt_path"))

    if admitted["activation_bundle_hash"] != activation_hash:
        fail("admitted receipt does not match chain activation_bundle_hash")
    if failed["activation_bundle_hash"] != activation_hash:
        fail("fail-closed receipt does not match chain activation_bundle_hash")
    if admitted["activation_bundle_hash"] != failed["activation_bundle_hash"]:
        fail("paired receipts must share the same activation_bundle_hash")

    if admitted["admission_decision"] != chain["expected_admitted_decision"]:
        fail("admitted receipt decision mismatch")
    if failed["admission_decision"] != chain["expected_fail_closed_decision"]:
        fail("fail-closed receipt decision mismatch")
    if admitted["admission_decision"] == failed["admission_decision"]:
        fail("paired receipts must diverge in admission_decision")
    if admitted["evidence_status"] != "complete":
        fail("admitted divergence fixture must have complete evidence")
    if failed["admission_decision"] != "fail-closed":
        fail("second divergence fixture must fail closed")
    if not failed.get("fail_closed_reason"):
        fail("fail-closed divergence fixture requires fail_closed_reason")

    differences = require_list(chain, "required_context_differences")
    for field in differences:
        if admitted.get(field) == failed.get(field):
            fail(f"required context field did not differ: {field}")

    boundary = chain.get("operator_boundary")
    if not isinstance(boundary, dict):
        fail("operator_boundary must be an object")
    for key in (
        "same_activation_bundle_is_not_same_runtime_context",
        "fail_closed_context_requires_fail_closed_reason",
        "replay_artifacts_must_remain_distinguishable",
        "policy_context_is_admission_boundary",
    ):
        if boundary.get(key) is not True:
            fail(f"operator_boundary.{key} must be true")

    lineage = failed.get("lineage", {})
    previous = lineage.get("previous_receipt_refs", []) if isinstance(lineage, dict) else []
    if admitted["receipt_id"] not in previous:
        fail("fail-closed receipt lineage must reference admitted receipt")


def load_receipt(path_value: str) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    receipt = validate_semantic_activation_receipt.load_json(path)
    schema = validate_semantic_activation_receipt.load_json(validate_semantic_activation_receipt.SCHEMA)
    validate_semantic_activation_receipt.validate_schema_contract(schema)
    validate_semantic_activation_receipt.validate_receipt(receipt)
    return receipt


def main(argv: list[str]) -> int:
    path = DEFAULT_CHAIN if len(argv) == 1 else Path(argv[1])
    try:
        validate_chain(load_json(path))
    except (ValidationError, validate_semantic_activation_receipt.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {path} validates as SemanticActivationContextDivergenceProof v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
