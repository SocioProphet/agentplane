#!/usr/bin/env python3
"""Validate AgentPlane guardrail evidence artifact schemas.

This intentionally uses only the Python standard library so the repo's normal
`make validate` path does not gain a new dependency. It performs structural
checks on the schema contracts and validates minimal representative artifacts
for the new guardrail evidence lane.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"

POLICY_DECISION_SCHEMA = SCHEMAS / "policy-decision-artifact.schema.v0.1.json"
STOP_GATE_SCHEMA = SCHEMAS / "stop-gate-artifact.schema.v0.1.json"


def die(message: str) -> None:
    print(f"[guardrail-evidence] ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        die(f"missing schema: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        die(f"schema must be an object: {path}")
    return data


def require_keys(obj: dict[str, Any], keys: list[str], path: str) -> None:
    for key in keys:
        if key not in obj:
            die(f"{path}.{key} is required")


def require_required_fields(schema: dict[str, Any], fields: list[str], path: str) -> None:
    required = schema.get("required")
    if not isinstance(required, list):
        die(f"{path}.required must be a list")
    missing = [field for field in fields if field not in required]
    if missing:
        die(f"{path}.required missing fields: {missing}")


def require_enum(schema: dict[str, Any], property_name: str, expected: set[str], path: str) -> None:
    properties = schema.get("properties") or {}
    prop = properties.get(property_name) or {}
    values = prop.get("enum")
    if not isinstance(values, list):
        die(f"{path}.properties.{property_name}.enum must be present")
    missing = expected.difference(set(values))
    if missing:
        die(f"{path}.properties.{property_name}.enum missing values: {sorted(missing)}")


def sample_policy_decision_artifact() -> dict[str, Any]:
    return {
        "kind": "PolicyDecisionArtifact",
        "bundle": "example-agent@0.1.0",
        "capturedAt": "2026-05-05T00:00:00Z",
        "sessionRef": "urn:srcos:session:example",
        "taskRef": "urn:srcos:task:example",
        "source": {
            "system": "guardrail-fabric",
            "adapter": "claude-code",
            "version": "0.1.0",
            "repoRef": "SocioProphet/guardrail-fabric",
            "commit": "sha-example",
        },
        "decision": {
            "schema": "sourceos.guardrail.decision.v0.1",
            "decisionId": "decision-1",
            "timestamp": "2026-05-05T00:00:00Z",
            "policyId": "sourceos/shell/block-privilege-escalation",
            "policyVersion": "0.1.0",
            "policyHash": None,
            "scope": "runtime",
            "severity": "critical",
            "decision": "deny",
            "reason": "Privilege escalation is blocked.",
            "remediation": "Use an approved executor profile.",
            "evidence": {
                "tool": "Bash",
                "actionClass": "shell",
                "inputDigest": "sha256:example",
            },
            "effects": {
                "agentMayContinue": False,
                "requiresHumanApproval": False,
            },
        },
        "result": "blocked",
        "artifactRefs": {
            "decisionLogRef": ".sourceos/logs/guardrail-decisions.jsonl",
            "toolEventRef": None,
            "redactionRef": None,
            "humanOverrideRef": None,
        },
        "governanceContext": None,
    }


def sample_stop_gate_artifact() -> dict[str, Any]:
    return {
        "kind": "StopGateArtifact",
        "bundle": "example-agent@0.1.0",
        "capturedAt": "2026-05-05T00:00:00Z",
        "sessionRef": "urn:srcos:session:example",
        "taskRef": "urn:srcos:task:example",
        "gateId": "sourceos.default.agent-completion",
        "gateName": "SourceOS Default Agent Completion Gate",
        "gatePolicyRef": "sourceos/agentplane/default-stop-gates@0.1.0",
        "result": "fail",
        "summary": "CI status is missing and branch is not pushed.",
        "checks": [
            {
                "checkId": "branch-pushed",
                "name": "Branch pushed",
                "result": "fail",
                "required": True,
                "reason": "No remote branch evidence was found.",
                "remediation": "Push the branch and re-run the stop gate.",
                "evidenceRefs": [],
                "relatedPolicyDecisionRefs": [],
            }
        ],
        "humanOverrideRef": None,
        "artifactRefs": {
            "policyDecisionArtifactRefs": ["policy-decision-artifact.json"],
            "runArtifactRef": None,
            "replayArtifactRef": None,
            "pullRequestRef": None,
            "ciStatusRef": None,
            "summaryRef": None,
        },
        "governanceContext": None,
    }


def validate_policy_decision_schema(schema: dict[str, Any]) -> None:
    require_keys(schema, ["$schema", "title", "type", "required", "properties"], "PolicyDecisionArtifact")
    require_required_fields(
        schema,
        ["kind", "bundle", "capturedAt", "sessionRef", "source", "decision", "result"],
        "PolicyDecisionArtifact",
    )
    require_enum(schema, "result", {"allow", "blocked", "needs_human", "redacted", "quarantined", "deferred"}, "PolicyDecisionArtifact")
    decision = ((schema.get("properties") or {}).get("decision") or {})
    require_required_fields(
        decision,
        ["schema", "decisionId", "timestamp", "policyId", "policyVersion", "scope", "severity", "decision", "reason", "remediation", "evidence", "effects"],
        "PolicyDecisionArtifact.decision",
    )


def validate_stop_gate_schema(schema: dict[str, Any]) -> None:
    require_keys(schema, ["$schema", "title", "type", "required", "properties"], "StopGateArtifact")
    require_required_fields(
        schema,
        ["kind", "bundle", "capturedAt", "sessionRef", "gateId", "gateName", "result", "checks"],
        "StopGateArtifact",
    )
    require_enum(schema, "result", {"pass", "fail", "needs_human", "waived", "not_applicable"}, "StopGateArtifact")


def validate_sample_against_top_level(schema: dict[str, Any], sample: dict[str, Any], path: str) -> None:
    require_required_fields(schema, list(schema.get("required") or []), path)
    require_keys(sample, list(schema.get("required") or []), f"sample {path}")
    kind_schema = ((schema.get("properties") or {}).get("kind") or {})
    expected_kind = kind_schema.get("const")
    if expected_kind and sample.get("kind") != expected_kind:
        die(f"sample {path}.kind must be {expected_kind}")


def main() -> int:
    policy_schema = load_json(POLICY_DECISION_SCHEMA)
    stop_gate_schema = load_json(STOP_GATE_SCHEMA)

    validate_policy_decision_schema(policy_schema)
    validate_stop_gate_schema(stop_gate_schema)
    validate_sample_against_top_level(policy_schema, sample_policy_decision_artifact(), "PolicyDecisionArtifact")
    validate_sample_against_top_level(stop_gate_schema, sample_stop_gate_artifact(), "StopGateArtifact")

    print("[guardrail-evidence] OK: guardrail evidence artifact schemas validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
