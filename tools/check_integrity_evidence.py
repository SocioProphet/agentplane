#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


class Bad(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Bad("expected object")
    return data


def need_str(obj: dict[str, Any], key: str) -> str:
    val = obj.get(key)
    if not isinstance(val, str) or not val:
        raise Bad(f"{key} must be non-empty string")
    return val


def need_hash(value: str, key: str) -> None:
    if not value.startswith("sha256:"):
        raise Bad(f"{key} must start with sha256:")


def check_path(path: str, root: str) -> None:
    if path.startswith("/") or path == ".." or path.startswith("../") or "/../" in path:
        raise Bad("path outside declared root")
    if root and not (path == root or path.startswith(root.rstrip("/") + "/")):
        raise Bad("path does not match declared root")


def check_request(obj: dict[str, Any]) -> None:
    for key in [
        "schemaVersion",
        "recordType",
        "request_id",
        "run_id",
        "attempt_id",
        "boundary_ref",
        "admission_ref",
        "authority_state_ref",
        "authority_status",
        "safe_root",
        "requested_by_ref",
        "requested_at",
        "receipt_hash",
    ]:
        need_str(obj, key)
    if obj["schemaVersion"] != "agentplane.integrity-evidence-request.v0.1":
        raise Bad("bad schemaVersion")
    if obj["recordType"] != "IntegrityEvidenceRequest":
        raise Bad("bad recordType")
    if not obj["admission_ref"].startswith("attempt-admission-receipt:"):
        raise Bad("bad admission_ref")
    if obj["authority_status"] in {"suspended", "revoked"}:
        raise Bad("bad authority_status")
    need_hash(obj["receipt_hash"], "receipt_hash")
    paths = obj.get("path_set")
    if not isinstance(paths, list) or not paths:
        raise Bad("path_set required")
    for item in paths:
        if not isinstance(item, dict):
            raise Bad("path item must be object")
        path = need_str(item, "path")
        before = need_str(item, "before_digest")
        expected = need_str(item, "expected_digest")
        check_path(path, obj["safe_root"])
        need_hash(before, "before_digest")
        need_hash(expected, "expected_digest")


def check_result(obj: dict[str, Any]) -> None:
    for key in [
        "schemaVersion",
        "recordType",
        "result_id",
        "request_ref",
        "run_id",
        "attempt_id",
        "boundary_ref",
        "admission_ref",
        "authority_state_ref",
        "safe_root",
        "status",
        "recorded_at",
        "receipt_hash",
    ]:
        need_str(obj, key)
    if obj["schemaVersion"] != "agentplane.integrity-evidence-result.v0.1":
        raise Bad("bad schemaVersion")
    if obj["recordType"] != "IntegrityEvidenceResult":
        raise Bad("bad recordType")
    if obj["status"] not in {"recorded", "denied", "invalid", "fail-closed"}:
        raise Bad("bad status")
    need_hash(obj["receipt_hash"], "receipt_hash")
    items = obj.get("path_results")
    if not isinstance(items, list) or not items:
        raise Bad("path_results required")
    for item in items:
        if not isinstance(item, dict):
            raise Bad("path result must be object")
        path = need_str(item, "path")
        before = need_str(item, "before_digest")
        observed = need_str(item, "observed_digest")
        expected = need_str(item, "expected_digest")
        check_path(path, obj["safe_root"])
        need_hash(before, "before_digest")
        need_hash(observed, "observed_digest")
        need_hash(expected, "expected_digest")
        if item.get("matches_expected") is not (observed == expected):
            raise Bad("bad match flag")
        if obj["status"] == "recorded" and observed != expected:
            raise Bad("bad recorded result")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_integrity_evidence.py <json>", file=sys.stderr)
        return 2
    try:
        obj = load(Path(argv[1]))
        if obj.get("recordType") == "IntegrityEvidenceRequest":
            check_request(obj)
        elif obj.get("recordType") == "IntegrityEvidenceResult":
            check_result(obj)
        else:
            raise Bad("unsupported recordType")
    except (OSError, json.JSONDecodeError, Bad) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as integrity evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
