#!/usr/bin/env python3
"""Validate rollback boundary/result receipt fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_SCHEMA = ROOT / "schemas" / "receipts" / "rollback-boundary.v0.1.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "receipts" / "rollback-result.v0.1.schema.json"

BOUNDARY_REQUIRED = {
    "schemaVersion",
    "recordType",
    "boundary_id",
    "run_id",
    "attempt_id",
    "repo_root",
    "captured_at",
    "strategy",
    "head_ref",
    "tracked_dirty_files",
    "untracked_files",
    "snapshots",
    "receipt_hash",
}

RESULT_REQUIRED = {
    "schemaVersion",
    "recordType",
    "result_id",
    "boundary_ref",
    "run_id",
    "attempt_id",
    "attempted",
    "status",
    "recorded_at",
    "before",
    "after",
    "receipt_hash",
}

RESULT_STATUS = {"restored", "not_required", "failed", "unavailable"}


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


def require_bool(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        fail(f"{key}: expected boolean")
    return value


def require_list(record: dict[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list):
        fail(f"{key}: expected list")
    return value


def validate_schema_contract(schema: dict[str, Any], kind: str) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail(f"{kind} schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail(f"{kind} schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail(f"{kind} schema must be strict")


def validate_boundary(record: dict[str, Any]) -> None:
    missing = sorted(BOUNDARY_REQUIRED - set(record))
    if missing:
        fail(f"rollback boundary missing required fields: {missing}")
    if record["schemaVersion"] != "agentplane.rollback-boundary.v0.1":
        fail("rollback boundary schemaVersion mismatch")
    if record["recordType"] != "RollbackBoundary":
        fail("rollback boundary recordType mismatch")
    for key in ("boundary_id", "run_id", "attempt_id", "repo_root", "captured_at", "strategy", "head_ref", "receipt_hash"):
        require_string(record, key)
    if not record["receipt_hash"].startswith("sha256:"):
        fail("rollback boundary receipt_hash must be sha256-bound")
    if _unsafe_path(record["repo_root"], allow_dot=True):
        fail(f"repo_root must be a safe relative path: {record['repo_root']}")
    if record["strategy"] not in {"git_head_plus_snapshot", "unavailable"}:
        fail(f"unknown rollback boundary strategy: {record['strategy']}")
    for key in ("tracked_dirty_files", "untracked_files"):
        for index, path in enumerate(require_list(record, key)):
            require_safe_path(path, f"{key}[{index}]")
    snapshots = require_list(record, "snapshots")
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, dict):
            fail(f"snapshots[{index}]: expected object")
        path = require_string(snapshot, "path")
        require_safe_path(path, f"snapshots[{index}].path")
        if not isinstance(snapshot.get("existed"), bool):
            fail(f"snapshots[{index}].existed must be boolean")
        if snapshot.get("encoding") != "base64":
            fail(f"snapshots[{index}].encoding must be base64")
        if snapshot.get("existed") is True and not snapshot.get("content_base64"):
            fail(f"snapshots[{index}].content_base64 required when existed=true")


def validate_result(record: dict[str, Any]) -> None:
    missing = sorted(RESULT_REQUIRED - set(record))
    if missing:
        fail(f"rollback result missing required fields: {missing}")
    if record["schemaVersion"] != "agentplane.rollback-result.v0.1":
        fail("rollback result schemaVersion mismatch")
    if record["recordType"] != "RollbackResult":
        fail("rollback result recordType mismatch")
    for key in ("result_id", "boundary_ref", "run_id", "attempt_id", "status", "recorded_at", "receipt_hash"):
        require_string(record, key)
    if not record["receipt_hash"].startswith("sha256:"):
        fail("rollback result receipt_hash must be sha256-bound")
    attempted = require_bool(record, "attempted")
    status = record["status"]
    if status not in RESULT_STATUS:
        fail(f"unknown rollback result status: {status}")
    if status in {"failed", "unavailable"} and not record.get("error"):
        fail(f"rollback result status={status} requires error evidence")
    if status == "restored" and not attempted:
        fail("rollback result status=restored requires attempted=true")
    for state_key in ("before", "after"):
        state = record.get(state_key)
        if not isinstance(state, dict):
            fail(f"{state_key}: expected object")
        for list_key in ("tracked_dirty_files", "untracked_files"):
            if list_key not in state:
                fail(f"{state_key}.{list_key} required")
            for index, path in enumerate(state[list_key]):
                require_safe_path(path, f"{state_key}.{list_key}[{index}]")
    for index, path in enumerate(record.get("changed_paths", [])):
        require_safe_path(path, f"changed_paths[{index}]")


def require_safe_path(path: Any, label: str) -> None:
    if not isinstance(path, str) or not path:
        fail(f"{label}: expected non-empty string")
    if _unsafe_path(path, allow_dot=False):
        fail(f"{label}: unsafe path {path!r}")


def _unsafe_path(value: str, *, allow_dot: bool) -> bool:
    normalized = value.replace("\\", "/")
    if allow_dot and normalized == ".":
        return False
    return normalized.startswith("/") or normalized == ".." or normalized.startswith("../") or "/../" in normalized


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in {"boundary", "result"}:
        print("usage: validate_rollback_receipts.py boundary|result <fixture.json>", file=sys.stderr)
        return 2
    mode = argv[1]
    fixture = Path(argv[2])
    try:
        if mode == "boundary":
            validate_schema_contract(load_json(BOUNDARY_SCHEMA), "rollback boundary")
            validate_boundary(load_json(fixture))
        else:
            validate_schema_contract(load_json(RESULT_SCHEMA), "rollback result")
            validate_result(load_json(fixture))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[2]} validates as rollback {mode} receipt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
