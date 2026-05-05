#!/usr/bin/env python3
"""Validate AgenticPRWorkOrder schema and example.

This bootstrap validator is intentionally stdlib-only. It catches malformed JSON,
missing schema/example files, wrong kind declarations, missing authority split,
and scope-policy regressions without adding runtime dependencies to AgentPlane.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "agentic-pr-work-order.schema.v0.1.json"
EXAMPLE = ROOT / "examples" / "agentic-pr-work-order.example.json"

REQUIRED_TOP_LEVEL = {"apiVersion", "kind", "metadata", "spec"}
REQUIRED_METADATA = {"name", "repository", "issueRef", "createdAt"}
REQUIRED_SPEC = {"objective", "authority", "scope", "nonGoals", "allowedSideEffects", "validation", "review", "output", "policyRefs", "ledger"}
REQUIRED_AUTHORITY = {"implementationAgent", "reviewAgent", "mergeGate", "separationOfDuties"}
REQUIRED_SCOPE = {"summary", "expectedFiles", "maxChangedFiles", "changedFileAllowance", "allowedPaths", "deniedPaths"}
REQUIRED_PR_SECTIONS = {"summary", "changed-files", "validation", "known-gaps", "self-critique", "linked-issue", "policy-evidence"}
REQUIRED_LEDGER_FIELDS = {"issueRef", "branch", "headSha", "changedFiles", "validationCommands", "reviewDecision", "mergeDecision"}
DENIED_PATH_PREFIXES = {".venv/", ".venv-tools/", "venv/", "node_modules/", ".mypy_cache/", ".pytest_cache/", "__pycache__/", "dist/", "build/"}
ALLOWED_SIDE_EFFECTS = {"create-branch", "commit-files", "open-draft-pr", "comment-on-issue", "read-ci-status", "request-review"}


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
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema must use JSON Schema draft 2020-12")
    require(schema.get("title") == "Agentic PR Work Order", "schema title mismatch")
    properties = schema.get("properties", {})
    require(properties.get("apiVersion", {}).get("const") == "agentplane.socioprophet.org/v0.1", "schema apiVersion const mismatch")
    require(properties.get("kind", {}).get("const") == "AgenticPRWorkOrder", "schema kind const mismatch")


def validate_example(example: dict[str, Any]) -> None:
    missing_top = REQUIRED_TOP_LEVEL - set(example)
    require(not missing_top, f"example missing top-level fields: {sorted(missing_top)}")
    require(example.get("apiVersion") == "agentplane.socioprophet.org/v0.1", "example apiVersion mismatch")
    require(example.get("kind") == "AgenticPRWorkOrder", "example kind mismatch")

    metadata = example.get("metadata")
    require(isinstance(metadata, dict), "metadata must be an object")
    missing_metadata = REQUIRED_METADATA - set(metadata)
    require(not missing_metadata, f"metadata missing fields: {sorted(missing_metadata)}")
    require(metadata.get("repository") == "SocioProphet/agentplane", "example repository must target SocioProphet/agentplane")
    require(str(metadata.get("issueRef", "")).endswith("/issues/82"), "example issueRef must point to agentplane#82")

    spec = example.get("spec")
    require(isinstance(spec, dict), "spec must be an object")
    missing_spec = REQUIRED_SPEC - set(spec)
    require(not missing_spec, f"spec missing fields: {sorted(missing_spec)}")

    authority = spec.get("authority")
    require(isinstance(authority, dict), "authority must be an object")
    missing_authority = REQUIRED_AUTHORITY - set(authority)
    require(not missing_authority, f"authority missing fields: {sorted(missing_authority)}")
    require(authority.get("separationOfDuties") is True, "separationOfDuties must be true")
    actors = {authority.get("implementationAgent"), authority.get("reviewAgent"), authority.get("mergeGate")}
    require(len(actors) == 3, "implementationAgent, reviewAgent, and mergeGate must be distinct")

    scope = spec.get("scope")
    require(isinstance(scope, dict), "scope must be an object")
    missing_scope = REQUIRED_SCOPE - set(scope)
    require(not missing_scope, f"scope missing fields: {sorted(missing_scope)}")
    expected_files = set(scope.get("expectedFiles", []))
    require("schemas/agentic-pr-work-order.schema.v0.1.json" in expected_files, "expectedFiles must include work-order schema")
    require("examples/agentic-pr-work-order.example.json" in expected_files, "expectedFiles must include work-order example")
    require(scope.get("maxChangedFiles", 0) >= len(expected_files), "maxChangedFiles must cover expectedFiles")
    denied_paths = set(scope.get("deniedPaths", []))
    missing_denied = sorted(DENIED_PATH_PREFIXES - denied_paths)
    require(not missing_denied, f"scope.deniedPaths missing defaults: {missing_denied}")

    side_effects = set(spec.get("allowedSideEffects", []))
    require(side_effects <= ALLOWED_SIDE_EFFECTS, f"unexpected allowed side effects: {sorted(side_effects - ALLOWED_SIDE_EFFECTS)}")
    require("open-draft-pr" in side_effects, "allowedSideEffects must include open-draft-pr")

    validation = spec.get("validation", {})
    commands = set(validation.get("requiredCommands", []))
    require("git status --short" in commands, "validation must require git status --short")
    require("git diff --stat" in commands, "validation must require git diff --stat")
    require(validation.get("evidenceRequired") is True, "validation.evidenceRequired must be true")

    review = spec.get("review", {})
    require(review.get("reviewerMode") == "adversarial", "reviewerMode must be adversarial")
    checklist = review.get("checklist", [])
    require(any("virtual environment" in item for item in checklist), "review checklist must mention virtual environment hygiene")

    output = spec.get("output", {})
    require(output.get("draftPrRequired") is True, "draftPrRequired must be true")
    missing_sections = sorted(REQUIRED_PR_SECTIONS - set(output.get("requiredPrSections", [])))
    require(not missing_sections, f"output.requiredPrSections missing: {missing_sections}")

    policy_refs = spec.get("policyRefs", {})
    require(policy_refs.get("diffHygieneGate") == "SocioProphet/policy-fabric#44", "policyRefs.diffHygieneGate must point to policy-fabric#44")
    require(str(policy_refs.get("pairedIssueRef", "")).endswith("/issues/44"), "pairedIssueRef must point to policy-fabric#44")

    ledger = spec.get("ledger", {})
    require(ledger.get("required") is True, "ledger.required must be true")
    missing_ledger = sorted(REQUIRED_LEDGER_FIELDS - set(ledger.get("fields", [])))
    require(not missing_ledger, f"ledger.fields missing: {missing_ledger}")


def main() -> int:
    try:
        validate_schema(load_json(SCHEMA))
        validate_example(load_json(EXAMPLE))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: validated AgenticPRWorkOrder schema and example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())