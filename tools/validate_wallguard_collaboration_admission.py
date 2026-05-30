#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "wallguard-collaboration-admission.v0.1.schema.json"
VALID = ROOT / "tests" / "fixtures" / "receipts" / "wallguard-collaboration-admission.same-wall.valid.json"
INVALIDS = [
    ROOT / "tests" / "fixtures" / "receipts" / "wallguard-collaboration-admission.cross-wall.invalid.json",
    ROOT / "tests" / "fixtures" / "receipts" / "wallguard-collaboration-admission.missing-context.invalid.json",
]

REQUIRED = {
    "schemaVersion",
    "recordType",
    "receipt_id",
    "collaboration_request_id",
    "source_agent_wall_context_ref",
    "target_agent_wall_context_ref",
    "source_wall_ref",
    "target_wall_ref",
    "collaboration_action",
    "admitted",
    "admission_decision",
    "reason_code",
    "wall_decision_ref",
    "wall_decision_outcome",
    "receipt_hash",
    "issued_at",
}

class ValidationError(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: root must be object")
    return data


def check(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        raise ValidationError(f"missing fields: {missing}")
    if record["schemaVersion"] != "agentplane.wallguard-collaboration-admission.v0.1":
        raise ValidationError("schemaVersion mismatch")
    if record["recordType"] != "WallGuardCollaborationAdmissionReceipt":
        raise ValidationError("recordType mismatch")
    if not isinstance(record["admitted"], bool):
        raise ValidationError("admitted must be boolean")
    if not str(record["receipt_hash"]).startswith("sha256:"):
        raise ValidationError("receipt_hash must use sha256 prefix")

    source_wall = record["source_wall_ref"]
    target_wall = record["target_wall_ref"]
    admitted = record["admitted"]
    decision = record["admission_decision"]
    reason = record["reason_code"]
    wall_outcome = record["wall_decision_outcome"]

    if admitted and decision != "admit":
        raise ValidationError("admitted=true requires admission_decision=admit")
    if decision == "admit" and not admitted:
        raise ValidationError("admit decision requires admitted=true")
    if admitted and wall_outcome != "allow":
        raise ValidationError("admitted=true requires allow outcome")
    if admitted and source_wall != target_wall:
        raise ValidationError("collaboration across different wall refs cannot be admitted")
    if source_wall == "unknown" or target_wall == "unknown":
        if admitted or decision != "fail-closed":
            raise ValidationError("unknown wall context requires fail-closed non-admission")
    if source_wall != target_wall and reason == "same_wall_allowed":
        raise ValidationError("different wall refs cannot use same_wall_allowed")


def main() -> int:
    try:
        schema = load(SCHEMA)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ValidationError("schema draft mismatch")
        if set(schema.get("required", [])) != REQUIRED:
            raise ValidationError("schema required fields drift")
        check(load(VALID))
        for invalid in INVALIDS:
            try:
                check(load(invalid))
            except ValidationError:
                continue
            raise ValidationError(f"invalid fixture unexpectedly passed: {invalid.relative_to(ROOT)}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: wallguard collaboration admission fixtures validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
