#!/usr/bin/env python3
"""Validate AgentPlane GuardedInvocationArtifact schema and sample artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "guarded-invocation-artifact.schema.v0.1.json"


def die(message: str) -> None:
    print(f"[guarded-invocation-artifact] ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        die(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        die(f"expected JSON object in {path}")
    return data


def require_keys(obj: dict[str, Any], keys: list[str], path: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        die(f"{path} missing keys: {missing}")


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


def sample_artifact() -> dict[str, Any]:
    return {
        "kind": "GuardedInvocationArtifact",
        "bundle": "example-agent@0.1.0",
        "capturedAt": "2026-05-05T00:00:00Z",
        "sessionRef": "urn:srcos:session:sample",
        "taskRef": "urn:srcos:task:sample",
        "workcellArtifactRef": "guarded-workcell-artifact.json",
        "workspacePath": "/tmp/workspace",
        "command": {
            "argv": ["python3", "-c", "print('ok')"],
            "commandClass": "tool",
            "shell": False,
            "cwd": "/tmp/workspace",
        },
        "invocation": {
            "allowed": True,
            "startedAt": "2026-05-05T00:00:00Z",
            "completedAt": "2026-05-05T00:00:01Z",
            "exitCode": 0,
            "status": "success",
            "reason": "Command completed and stop gate passed or was waived.",
            "remediation": None,
        },
        "guardrail": {
            "decisionLogRef": ".sourceos/logs/guardrail-decisions.jsonl",
            "hookCommand": "guardrail-fabric-hook --write-log",
            "environment": {
                "AGENTPLANE_SESSION_REF": "urn:srcos:session:sample",
                "AGENTPLANE_TASK_REF": "urn:srcos:task:sample",
                "SOURCEOS_GUARDRAIL_DECISION_LOG": ".sourceos/logs/guardrail-decisions.jsonl",
                "SOURCEOS_STOP_GATE_ARTIFACT": ".sourceos/logs/stop-gate-artifact.json",
            },
        },
        "stopGate": {
            "required": True,
            "evaluated": True,
            "artifactRef": ".sourceos/logs/stop-gate-artifact.json",
            "result": "pass",
        },
        "result": "success",
        "sideEffects": {
            "localCommandExecuted": True,
            "agentProcessInvoked": False,
            "externalMutationPerformed": False,
            "remoteMutationPerformed": False,
            "providerContacted": False,
        },
        "artifactRefs": {
            "stdoutRef": ".sourceos/logs/invocations/sample/stdout.txt",
            "stderrRef": ".sourceos/logs/invocations/sample/stderr.txt",
            "stopGateArtifactRef": ".sourceos/logs/stop-gate-artifact.json",
            "runArtifactRef": None,
            "replayArtifactRef": None,
        },
        "governanceContext": {
            "invocationDir": ".sourceos/logs/invocations/sample",
            "sideEffectsAllowed": True,
            "requiresStopGateForSuccess": True,
        },
    }


def validate_sample(sample: dict[str, Any], schema: dict[str, Any]) -> None:
    require_keys(sample, list(schema.get("required") or []), "sample GuardedInvocationArtifact")
    if sample["kind"] != "GuardedInvocationArtifact":
        die("sample kind must be GuardedInvocationArtifact")
    if sample["sideEffects"]["remoteMutationPerformed"] is not False:
        die("sample must not record remote mutation")
    if sample["sideEffects"]["providerContacted"] is not False:
        die("sample must not record provider contact")
    if sample["stopGate"]["result"] not in {"pass", "waived"}:
        die("sample success must include a passing or waived stop gate")


def main() -> int:
    schema = load_json(SCHEMA)
    require_keys(schema, ["$schema", "title", "type", "required", "properties"], "GuardedInvocationArtifact schema")
    require_required_fields(
        schema,
        [
            "kind",
            "bundle",
            "capturedAt",
            "sessionRef",
            "taskRef",
            "workcellArtifactRef",
            "workspacePath",
            "command",
            "invocation",
            "guardrail",
            "stopGate",
            "result",
            "sideEffects",
            "artifactRefs",
        ],
        "GuardedInvocationArtifact",
    )
    require_enum(schema, "result", {"success", "failure", "blocked", "needs_human"}, "GuardedInvocationArtifact")
    validate_sample(sample_artifact(), schema)
    print("[guarded-invocation-artifact] OK: guarded invocation artifact schema validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
