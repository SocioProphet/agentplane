#!/usr/bin/env python3
"""Validate MeshRush execution candidate fixtures.

Dependency-light structural validation for v0.1 MeshRush adapter candidates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = sorted((ROOT / "examples/meshrush").glob("*.v0.1.json"))
REQUIRED = [
    "schemaVersion",
    "candidateId",
    "sourceArtifactRef",
    "contextRef",
    "requestedActionType",
    "approvalBoundary",
    "validationStatus",
    "approvalState",
    "evidenceRefs",
    "policyRefs",
    "claims",
    "replayRequirements",
    "rollbackSemantics",
    "classification",
]
VALID_BOUNDARIES = {"advisory", "approval_required", "executable", "blocked"}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        fail(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected object at top level: {path}")
    return value


def require_fields(doc: Dict[str, Any], fields: Iterable[str], path: Path) -> None:
    missing = [field for field in fields if field not in doc]
    if missing:
        fail(f"{path} missing required fields: {', '.join(missing)}")


def require_nonempty_array(doc: Dict[str, Any], field: str, path: Path) -> None:
    value = doc.get(field)
    if not isinstance(value, list) or not value:
        fail(f"{path} {field} must be a non-empty array")


def validate_candidate(path: Path, doc: Dict[str, Any]) -> None:
    require_fields(doc, REQUIRED, path)
    if doc.get("schemaVersion") != "v0.1":
        fail(f"{path} schemaVersion must be v0.1")
    boundary = doc.get("approvalBoundary")
    if boundary not in VALID_BOUNDARIES:
        fail(f"{path} approvalBoundary invalid: {boundary}")
    approval = doc.get("approvalState", {})
    if not isinstance(approval, dict):
        fail(f"{path} approvalState must be object")
    rollback = doc.get("rollbackSemantics", {})
    if not isinstance(rollback, dict):
        fail(f"{path} rollbackSemantics must be object")

    if boundary == "advisory":
        if approval.get("status") != "not_required":
            fail(f"{path} advisory candidates must have approvalState.status=not_required")
        if rollback.get("strategy") != "evidence_only":
            fail(f"{path} advisory candidates must use evidence_only rollback")

    if boundary == "approval_required":
        if approval.get("status") != "required":
            fail(f"{path} approval_required candidates must have approvalState.status=required")
        handling_tags = doc.get("handlingTags", [])
        if "approval-required" not in handling_tags:
            fail(f"{path} approval_required candidates must include approval-required handling tag")
        class_tags = doc.get("classification", {}).get("handlingTags", [])
        if "evidence-record-only" not in class_tags:
            fail(f"{path} approval_required demo candidate must remain evidence-record-only")

    for field in ["evidenceRefs", "policyRefs", "claims"]:
        require_nonempty_array(doc, field, path)


def main() -> int:
    if not FIXTURES:
        fail("no MeshRush candidate fixtures found")
    for fixture in FIXTURES:
        validate_candidate(fixture, load_json(fixture))
    print(f"validated {len(FIXTURES)} MeshRush execution candidate fixture(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
