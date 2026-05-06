#!/usr/bin/env python3
"""Deterministic smoke validator for AgentOperationContract schema and example.

Checks that:
- The schema has the expected title, kind const, required fields, and operation-type enum.
- The example is a valid AgentOperationContract with all required top-level fields.
- The example authority, lifecycle, policyGate, tasks, events, and artifacts are internally consistent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "agent-operation-contract.schema.v0.1.json"
EXAMPLE = ROOT / "examples" / "agent-operation-contract.example.json"

REQUIRED_OPERATION_TYPES = {
    "agent.patch.propose",
    "agent.report.create",
    "agent.metadata.fill",
    "agent.failure.explain",
    "agent.remediation.propose",
    "agent.terminal.assist",
}

REQUIRED_TOP_LEVEL = {
    "kind",
    "operationId",
    "operationType",
    "capturedAt",
    "authority",
    "lifecycle",
    "tasks",
    "events",
    "artifacts",
    "policyGate",
}


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing {path.relative_to(ROOT)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"expected object in {path.relative_to(ROOT)}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[agent-operation-contract] FAIL: {message}")


def validate_schema(schema: dict) -> None:
    require(
        schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        "schema $schema must be json-schema 2020-12",
    )
    require(
        schema.get("title") == "AgentOperationContract v0.1",
        "schema title must be 'AgentOperationContract v0.1'",
    )
    props = schema.get("properties", {})
    require(
        props.get("kind", {}).get("const") == "AgentOperationContract",
        "schema properties.kind.const must be 'AgentOperationContract'",
    )
    op_type_enum = set(props.get("operationType", {}).get("enum", []))
    require(
        REQUIRED_OPERATION_TYPES == op_type_enum,
        f"schema operationType enum must be {sorted(REQUIRED_OPERATION_TYPES)}, got {sorted(op_type_enum)}",
    )
    required_fields = set(schema.get("required", []))
    for field in REQUIRED_TOP_LEVEL:
        require(field in required_fields, f"schema required[] must include '{field}'")


def validate_example(example: dict) -> None:
    require(example.get("kind") == "AgentOperationContract", "example kind must be AgentOperationContract")

    for field in REQUIRED_TOP_LEVEL:
        require(field in example, f"example missing required field '{field}'")

    require(
        example.get("operationType") in REQUIRED_OPERATION_TYPES,
        f"example operationType must be one of {sorted(REQUIRED_OPERATION_TYPES)}",
    )
    require(
        isinstance(example.get("operationId"), str) and example["operationId"],
        "example operationId must be a non-empty string",
    )
    require(
        isinstance(example.get("capturedAt"), str) and example["capturedAt"],
        "example capturedAt must be a non-empty string",
    )

    authority = example.get("authority", {})
    require(isinstance(authority, dict), "example authority must be an object")
    require(
        isinstance(authority.get("actingFor"), str) and authority["actingFor"],
        "example authority.actingFor must be a non-empty string",
    )
    require(
        isinstance(authority.get("scope"), list) and len(authority["scope"]) > 0,
        "example authority.scope must be a non-empty list",
    )
    require(
        authority.get("auditLevel") in {"full", "summary", "minimal"},
        "example authority.auditLevel must be 'full', 'summary', or 'minimal'",
    )

    lifecycle = example.get("lifecycle", {})
    require(isinstance(lifecycle, dict), "example lifecycle must be an object")
    require(
        lifecycle.get("status") in {"created", "in-progress", "completed", "failed", "cancelled", "compensating"},
        "example lifecycle.status must be a valid lifecycle status",
    )
    require(
        isinstance(lifecycle.get("idempotencyKey"), str) and lifecycle["idempotencyKey"],
        "example lifecycle.idempotencyKey must be a non-empty string",
    )
    require(
        isinstance(lifecycle.get("retryable"), bool),
        "example lifecycle.retryable must be a boolean",
    )
    require(
        isinstance(lifecycle.get("retryCount"), int) and lifecycle["retryCount"] >= 0,
        "example lifecycle.retryCount must be a non-negative integer",
    )

    tasks = example.get("tasks", [])
    require(isinstance(tasks, list), "example tasks must be an array")
    for i, task in enumerate(tasks):
        require(isinstance(task.get("taskId"), str) and task["taskId"], f"tasks[{i}].taskId must be non-empty")
        require(isinstance(task.get("taskType"), str) and task["taskType"], f"tasks[{i}].taskType must be non-empty")
        require(
            task.get("status") in {"pending", "running", "completed", "failed", "cancelled", "skipped"},
            f"tasks[{i}].status must be a valid task status",
        )

    events = example.get("events", [])
    require(isinstance(events, list), "example events must be an array")
    require(len(events) > 0, "example events must contain at least one event")
    valid_event_types = {
        "created", "updated", "retried", "cancelled", "artifact_emitted",
        "gate_evaluated", "completed", "failed", "compensation_started", "compensation_completed",
    }
    for i, event in enumerate(events):
        require(isinstance(event.get("eventId"), str) and event["eventId"], f"events[{i}].eventId must be non-empty")
        require(
            event.get("eventType") in valid_event_types,
            f"events[{i}].eventType must be a valid event type, got {event.get('eventType')!r}",
        )
        require(isinstance(event.get("emittedAt"), str) and event["emittedAt"], f"events[{i}].emittedAt must be non-empty")

    artifacts = example.get("artifacts", [])
    require(isinstance(artifacts, list), "example artifacts must be an array")
    valid_artifact_types = {"patch", "report", "document", "test-result", "terminal-transcript", "metadata-fill"}
    valid_admission_statuses = {"pending-review", "admitted", "rejected", "archived"}
    for i, art in enumerate(artifacts):
        require(isinstance(art.get("artifactId"), str) and art["artifactId"], f"artifacts[{i}].artifactId must be non-empty")
        require(
            art.get("artifactType") in valid_artifact_types,
            f"artifacts[{i}].artifactType must be a valid artifact type",
        )
        require(
            art.get("admissionStatus") in valid_admission_statuses,
            f"artifacts[{i}].admissionStatus must be a valid admission status",
        )
        require(isinstance(art.get("createdAt"), str) and art["createdAt"], f"artifacts[{i}].createdAt must be non-empty")

    policy_gate = example.get("policyGate", {})
    require(isinstance(policy_gate, dict), "example policyGate must be an object")
    require(isinstance(policy_gate.get("evaluated"), bool), "example policyGate.evaluated must be a boolean")
    require(
        policy_gate.get("result") in {"allow", "deny", "pending", "needs_human"},
        "example policyGate.result must be 'allow', 'deny', 'pending', or 'needs_human'",
    )


def main() -> int:
    schema = load(SCHEMA)
    example = load(EXAMPLE)
    validate_schema(schema)
    validate_example(example)
    print("OK: validated AgentOperationContract schema and example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
