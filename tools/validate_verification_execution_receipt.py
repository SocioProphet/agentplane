#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "verification-execution-receipt.v0.1.schema.json"

REQUIRED_FIELDS = {
    "schemaVersion",
    "recordType",
    "execution_id",
    "run_id",
    "attempt_id",
    "governed_run_contract_ref",
    "admission_receipt_ref",
    "preflight_receipt_ref",
    "authority_state_ref",
    "verifier_command_ref",
    "verifier_command",
    "safety_context",
    "execution_status",
    "started_at",
    "ended_at",
    "exit_code",
    "stdout_ref",
    "stderr_ref",
    "artifact_refs",
    "receipt_hash",
}

COMMAND_REQUIRED = {"command", "allowlisted", "network_mode", "mutation_mode"}
SAFETY_REQUIRED = {"admission_decision", "preflight_outcome", "runtime_action", "authority_decision"}
STATUSES = {"completed", "failed", "skipped", "fail-closed"}


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


def req_str(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def req_obj(record: dict[str, Any], key: str) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict):
        fail(f"{key}: expected object")
    return value


def req_str_list(record: dict[str, Any], key: str) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key}: expected non-empty list")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            fail(f"{key}[{index}]: expected non-empty string")
    return value


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED_FIELDS - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing fields: {missing}")


def validate_receipt(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        fail(f"missing fields: {missing}")
    if record["schemaVersion"] != "agentplane.verification-execution-receipt.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "VerificationExecutionReceipt":
        fail("recordType mismatch")

    for key in REQUIRED_FIELDS - {"verifier_command", "safety_context", "artifact_refs", "exit_code"}:
        req_str(record, key)
    if not record["governed_run_contract_ref"].startswith("governed-run-contract:"):
        fail("governed_run_contract_ref prefix mismatch")
    if not record["admission_receipt_ref"].startswith("attempt-admission-receipt:"):
        fail("admission_receipt_ref prefix mismatch")
    if not record["preflight_receipt_ref"].startswith("preflight-receipt:"):
        fail("preflight_receipt_ref prefix mismatch")
    if not record["receipt_hash"].startswith("sha256:"):
        fail("receipt_hash prefix mismatch")
    if record["execution_status"] not in STATUSES:
        fail("execution_status invalid")
    if not isinstance(record.get("exit_code"), int) or isinstance(record.get("exit_code"), bool):
        fail("exit_code must be integer")
    if record["exit_code"] < 0:
        fail("exit_code must be non-negative")

    validate_command(req_obj(record, "verifier_command"))
    validate_safety(req_obj(record, "safety_context"))
    req_str_list(record, "artifact_refs")
    if record["execution_status"] in {"skipped", "fail-closed"} and not record.get("fail_closed_reason"):
        fail("fail_closed_reason required for skipped or fail-closed status")


def validate_command(command: dict[str, Any]) -> None:
    missing = sorted(COMMAND_REQUIRED - set(command))
    if missing:
        fail(f"verifier_command missing fields: {missing}")
    req_str(command, "command")
    if command.get("allowlisted") is not True:
        fail("verifier_command.allowlisted must be true")
    if command.get("network_mode") != "off":
        fail("verifier_command.network_mode must be off")
    if command.get("mutation_mode") != "none":
        fail("verifier_command.mutation_mode must be none")


def validate_safety(context: dict[str, Any]) -> None:
    missing = sorted(SAFETY_REQUIRED - set(context))
    if missing:
        fail(f"safety_context missing fields: {missing}")
    if context.get("admission_decision") != "admit":
        fail("admission_decision must be admit")
    if context.get("preflight_outcome") != "pass":
        fail("preflight_outcome must be pass")
    if context.get("runtime_action") != "allow":
        fail("runtime_action must be allow")
    if context.get("authority_decision") in {"suspended", "revoked"}:
        fail("authority_decision cannot be suspended or revoked")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_verification_execution_receipt.py <fixture.json>", file=sys.stderr)
        return 2
    try:
        validate_schema(load_json(SCHEMA))
        validate_receipt(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as VerificationExecutionReceipt v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
