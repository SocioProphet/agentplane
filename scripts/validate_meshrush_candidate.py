#!/usr/bin/env python3
"""Validate MeshRush execution candidate fixtures.

Dependency-light structural validation for the v0.1 MeshRush adapter candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/meshrush/soil-intelligence-advisory-candidate.v0.1.json"
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


def require_fields(doc: Dict[str, Any], fields: Iterable[str]) -> None:
    missing = [field for field in fields if field not in doc]
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")


def require_nonempty_array(doc: Dict[str, Any], field: str) -> None:
    value = doc.get(field)
    if not isinstance(value, list) or not value:
        fail(f"{field} must be a non-empty array")


def main() -> int:
    doc = load_json(FIXTURE)
    require_fields(doc, REQUIRED)
    if doc.get("schemaVersion") != "v0.1":
        fail("schemaVersion must be v0.1")
    if doc.get("approvalBoundary") == "advisory":
        approval = doc.get("approvalState", {})
        if not isinstance(approval, dict) or approval.get("status") != "not_required":
            fail("advisory candidates must have approvalState.status=not_required")
        rollback = doc.get("rollbackSemantics", {})
        if not isinstance(rollback, dict) or rollback.get("strategy") != "evidence_only":
            fail("advisory candidates must use evidence_only rollback")
    for field in ["evidenceRefs", "policyRefs", "claims"]:
        require_nonempty_array(doc, field)
    print("validated MeshRush execution candidate fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
