#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "original-attempt-context.v0.1.schema.json"

REQUIRED = {
    "schemaVersion",
    "recordType",
    "context_id",
    "original_attempt_ref",
    "original_attempt_phase",
    "side_effect_boundary",
    "retry_posture",
    "original_attempt_status_source",
    "recovery_policy_posture",
    "recorded_at",
    "receipt_hash",
}

PHASES_WITH_EXECUTION = {"started", "completed", "failed"}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        fail("expected object")
    return payload


def require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def optional_ref(record: dict[str, Any], key: str) -> str | None:
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string or null")
    return value


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.original-attempt-context.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "OriginalAttemptContext":
        fail("recordType const mismatch")


def validate_record(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"missing required fields: {missing}")

    if record.get("schemaVersion") != "agentplane.original-attempt-context.v0.1":
        fail("schemaVersion mismatch")
    if record.get("recordType") != "OriginalAttemptContext":
        fail("recordType mismatch")

    for key in ("context_id", "original_attempt_ref", "original_attempt_phase", "side_effect_boundary", "retry_posture", "original_attempt_status_source", "recovery_policy_posture", "recorded_at", "receipt_hash"):
        require_string(record, key)
    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")

    phase = record["original_attempt_phase"]
    boundary = record["side_effect_boundary"]
    retry = record["retry_posture"]
    policy = record["recovery_policy_posture"]
    source = record["original_attempt_status_source"]

    admission_ref = optional_ref(record, "original_admission_ref")
    execution_ref = optional_ref(record, "original_execution_ref")
    runtime_ref = optional_ref(record, "original_runtime_receipt_ref")
    verification_ref = optional_ref(record, "original_verification_receipt_ref")
    optional_ref(record, "original_preflight_ref")

    if phase == "queued":
        if any([admission_ref, execution_ref, runtime_ref, verification_ref]):
            fail("queued original attempt must not carry admission or execution receipt refs")
        if boundary != "none":
            fail("queued original attempt must have side_effect_boundary=none")
        if retry != "safe_retry" or policy != "eligible_for_retry":
            fail("queued + none must be safe retry / eligible for retry")
        if source != "queue_state":
            fail("queued original attempt must use queue_state source")

    if phase == "admitted":
        if not admission_ref:
            fail("admitted original attempt requires original_admission_ref")
        if execution_ref or runtime_ref or verification_ref:
            fail("admitted original attempt must not claim execution receipts")
        if retry == "safe_retry":
            fail("admitted original attempt must not be automatic safe retry")

    if phase in PHASES_WITH_EXECUTION:
        if not (execution_ref or runtime_ref or verification_ref):
            fail("started/completed/failed original attempt requires execution or runtime evidence ref")

    if phase == "completed":
        if boundary != "confirmed":
            fail("completed original attempt must have confirmed side-effect boundary")
        if retry != "do_not_retry" or policy != "blocked":
            fail("completed + confirmed must be do_not_retry / blocked")

    if boundary in {"possible", "confirmed"}:
        if retry == "safe_retry":
            fail("possible/confirmed side-effect boundary cannot be safe_retry")
        if policy == "eligible_for_retry":
            fail("possible/confirmed side-effect boundary cannot be eligible_for_retry")

    if boundary == "unknown" or phase == "unknown":
        if retry != "review_required" or policy != "requires_review":
            fail("unknown phase or boundary must require review")
        if source != "unknown":
            fail("unknown phase or boundary must use unknown status source")

    if retry == "review_required" and not record.get("review_reason"):
        fail("review_required requires review_reason")
    if retry == "do_not_retry" and not record.get("review_reason"):
        fail("do_not_retry requires review_reason")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_original_attempt_context.py <fixture.json>", file=sys.stderr)
        return 2
    try:
        validate_schema(load(SCHEMA))
        validate_record(load(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as OriginalAttemptContext v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
