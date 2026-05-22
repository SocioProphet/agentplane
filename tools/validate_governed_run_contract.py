#!/usr/bin/env python3
"""Validate GovernedRunContract v0.1 fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "runs" / "governed-run-contract.v0.1.schema.json"

REQUIRED_FIELDS = {
    "schemaVersion",
    "recordType",
    "run_id",
    "objective",
    "workspace_ref",
    "repo_root",
    "agent_ref",
    "authority_grant_ref",
    "policy_bundle_ref",
    "trustops_gate_policy_ref",
    "budget",
    "verification_plan",
    "allowed_paths",
    "denied_paths",
    "network_mode",
    "execution_profile",
    "mutation_mode",
    "rollback_required",
    "receipt_requirements",
}

REQUIRED_BUDGET_FIELDS = {"max_usd", "soft_limit_usd", "max_iterations", "max_tokens"}
REQUIRED_RECEIPTS = {
    "safety_preflight",
    "attempt_admission",
    "runtime_attempt",
    "verification_result",
    "run_dossier",
}
NETWORK_MODES = {"off", "allowlisted", "open"}
EXECUTION_PROFILES = {"strict_local", "ci_safe", "staging_controlled", "research_untrusted"}
MUTATION_MODES = {"verify_only", "mutation"}
VERIFIER_KINDS = {"lint", "typecheck", "test", "security", "custom"}


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


def validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    required = set(schema.get("required", []))
    missing = sorted(REQUIRED_FIELDS - required)
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.governed-run-contract.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "GovernedRunContract":
        fail("recordType const mismatch")


def validate_contract(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        fail(f"missing required fields: {missing}")

    if record["schemaVersion"] != "agentplane.governed-run-contract.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "GovernedRunContract":
        fail("recordType mismatch")

    for key in (
        "run_id",
        "objective",
        "workspace_ref",
        "repo_root",
        "agent_ref",
        "authority_grant_ref",
        "policy_bundle_ref",
        "trustops_gate_policy_ref",
        "network_mode",
        "execution_profile",
        "mutation_mode",
    ):
        require_string(record, key)

    if record["network_mode"] not in NETWORK_MODES:
        fail(f"invalid network_mode: {record['network_mode']}")
    if record["execution_profile"] not in EXECUTION_PROFILES:
        fail(f"invalid execution_profile: {record['execution_profile']}")
    if record["mutation_mode"] not in MUTATION_MODES:
        fail(f"invalid mutation_mode: {record['mutation_mode']}")

    validate_budget(record.get("budget"))
    validate_paths(record)
    validate_verification_plan(record)
    validate_receipt_requirements(record.get("receipt_requirements"))
    require_bool(record, "rollback_required")

    if record["mutation_mode"] == "mutation" and not record["rollback_required"]:
        fail("mutation runs require rollback_required=true")


def validate_budget(value: Any) -> None:
    if not isinstance(value, dict):
        fail("budget: expected object")
    missing = sorted(REQUIRED_BUDGET_FIELDS - set(value))
    if missing:
        fail(f"budget missing required fields: {missing}")
    max_usd = value.get("max_usd")
    soft_limit_usd = value.get("soft_limit_usd")
    max_iterations = value.get("max_iterations")
    max_tokens = value.get("max_tokens")
    if not isinstance(max_usd, (int, float)) or max_usd <= 0:
        fail("budget.max_usd must be positive")
    if not isinstance(soft_limit_usd, (int, float)) or soft_limit_usd <= 0:
        fail("budget.soft_limit_usd must be positive")
    if soft_limit_usd > max_usd:
        fail("budget.soft_limit_usd must be <= max_usd")
    if not isinstance(max_iterations, int) or max_iterations < 1:
        fail("budget.max_iterations must be >= 1")
    if not isinstance(max_tokens, int) or max_tokens < 1:
        fail("budget.max_tokens must be >= 1")


def validate_paths(record: dict[str, Any]) -> None:
    repo_root = record["repo_root"]
    if _unsafe_path(repo_root, allow_dot=True):
        fail(f"repo_root must be relative and inside the workspace: {repo_root}")
    for key in ("allowed_paths", "denied_paths", "allowed_network_domains"):
        if key in record:
            values = require_list(record, key)
            for index, value in enumerate(values):
                if not isinstance(value, str) or not value:
                    fail(f"{key}[{index}]: expected non-empty string")
                if key != "allowed_network_domains" and _unsafe_path(value, allow_dot=False):
                    fail(f"{key}[{index}] must be a safe relative pattern: {value}")
    if not record["allowed_paths"]:
        fail("allowed_paths must be non-empty")


def validate_verification_plan(record: dict[str, Any]) -> None:
    plan = require_list(record, "verification_plan")
    if record["mutation_mode"] == "mutation" and not plan:
        fail("mutation runs require a non-empty verification_plan")
    for index, step in enumerate(plan):
        if not isinstance(step, dict):
            fail(f"verification_plan[{index}]: expected object")
        command = step.get("command")
        kind = step.get("kind")
        if not isinstance(command, str) or not command:
            fail(f"verification_plan[{index}].command: expected non-empty string")
        if _command_looks_destructive(command):
            fail(f"verification_plan[{index}].command looks destructive")
        if kind not in VERIFIER_KINDS:
            fail(f"verification_plan[{index}].kind invalid: {kind}")
        required = step.get("required", True)
        if not isinstance(required, bool):
            fail(f"verification_plan[{index}].required must be boolean when present")


def validate_receipt_requirements(value: Any) -> None:
    if not isinstance(value, dict):
        fail("receipt_requirements: expected object")
    missing = sorted(REQUIRED_RECEIPTS - set(value))
    if missing:
        fail(f"receipt_requirements missing required fields: {missing}")
    for key in REQUIRED_RECEIPTS:
        if value.get(key) is not True:
            fail(f"receipt_requirements.{key} must be true")


def _unsafe_path(value: str, *, allow_dot: bool) -> bool:
    normalized = value.replace("\\", "/")
    if allow_dot and normalized == ".":
        return False
    return normalized.startswith("/") or normalized == ".." or normalized.startswith("../") or "/../" in normalized


def _command_looks_destructive(command: str) -> bool:
    lowered = command.lower()
    return any(token in lowered for token in ("rm -rf", "git reset --hard", "git clean -f", "sudo "))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_governed_run_contract.py <fixture.json>", file=sys.stderr)
        return 2

    try:
        validate_schema_contract(load_json(SCHEMA))
        validate_contract(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {argv[1]} validates as GovernedRunContract v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
