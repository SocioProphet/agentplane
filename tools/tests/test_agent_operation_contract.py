from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]
ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

MODULE_PATH = TOOLS_DIR / "validate_agent_operation_contract.py"
spec = importlib.util.spec_from_file_location("validate_agent_operation_contract", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["validate_agent_operation_contract"] = module
spec.loader.exec_module(module)

validate_schema = module.validate_schema
validate_example = module.validate_example
SCHEMA = module.SCHEMA
EXAMPLE = module.EXAMPLE
REQUIRED_OPERATION_TYPES = module.REQUIRED_OPERATION_TYPES


def make_valid_example(**overrides) -> dict:
    base = {
        "kind": "AgentOperationContract",
        "operationId": "op-test-001",
        "operationType": "agent.patch.propose",
        "bundle": "example-agent@0.1.0",
        "capturedAt": "2026-05-06T19:00:00Z",
        "authority": {
            "actingFor": "user:octocat",
            "scope": ["workspace:write"],
            "budget": None,
            "policyProfileRef": None,
            "auditLevel": "full",
        },
        "lifecycle": {
            "status": "completed",
            "startedAt": "2026-05-06T19:00:01Z",
            "completedAt": "2026-05-06T19:00:05Z",
            "idempotencyKey": "op-test-001/attempt-1",
            "retryable": True,
            "retryCount": 0,
            "cancellation": None,
            "compensation": None,
        },
        "tasks": [],
        "events": [{"eventId": "evt-001", "eventType": "created", "emittedAt": "2026-05-06T19:00:00Z", "data": None}],
        "artifacts": [],
        "decisionCard": None,
        "policyGate": {"evaluated": True, "result": "allow", "policyRef": None, "evaluatedAt": None, "reason": None},
        "replayRef": None,
        "ledgerRef": None,
        "governanceContext": None,
    }
    base.update(overrides)
    return base


class TestSchemaFile:
    def test_schema_file_exists(self) -> None:
        assert SCHEMA.exists(), f"missing schema: {SCHEMA}"

    def test_schema_is_valid_json(self) -> None:
        data = json.loads(SCHEMA.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_schema_passes_validate_schema(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validate_schema(schema)

    def test_schema_contains_all_operation_types(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        enum = set(schema["properties"]["operationType"]["enum"])
        assert enum == REQUIRED_OPERATION_TYPES

    def test_schema_rejects_missing_title(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        schema["title"] = "Wrong Title"
        with pytest.raises(SystemExit):
            validate_schema(schema)


class TestExampleFile:
    def test_example_file_exists(self) -> None:
        assert EXAMPLE.exists(), f"missing example: {EXAMPLE}"

    def test_example_is_valid_json(self) -> None:
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_example_passes_validate_example(self) -> None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        validate_example(example)

    def test_example_kind(self) -> None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        assert example["kind"] == "AgentOperationContract"

    def test_example_operation_type_is_supported(self) -> None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        assert example["operationType"] in REQUIRED_OPERATION_TYPES

    def test_example_artifacts_are_pending_review(self) -> None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        for art in example.get("artifacts", []):
            assert art["admissionStatus"] in {"pending-review", "admitted", "rejected", "archived"}

    def test_example_events_non_empty(self) -> None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        assert len(example["events"]) > 0


class TestValidateExample:
    def test_valid_minimal_example(self) -> None:
        validate_example(make_valid_example())

    def test_wrong_kind_rejected(self) -> None:
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(kind="WrongKind"))

    def test_invalid_operation_type_rejected(self) -> None:
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(operationType="agent.unknown.operation"))

    def test_all_supported_operation_types_pass(self) -> None:
        for op_type in REQUIRED_OPERATION_TYPES:
            validate_example(make_valid_example(operationType=op_type))

    def test_empty_events_rejected(self) -> None:
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(events=[]))

    def test_invalid_event_type_rejected(self) -> None:
        ex = make_valid_example(events=[{"eventId": "evt-001", "eventType": "invalid_event", "emittedAt": "2026-05-06T19:00:00Z", "data": None}])
        with pytest.raises(SystemExit):
            validate_example(ex)

    def test_invalid_lifecycle_status_rejected(self) -> None:
        lifecycle = make_valid_example()["lifecycle"].copy()
        lifecycle["status"] = "unknown-status"
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(lifecycle=lifecycle))

    def test_empty_scope_rejected(self) -> None:
        authority = make_valid_example()["authority"].copy()
        authority["scope"] = []
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(authority=authority))

    def test_invalid_audit_level_rejected(self) -> None:
        authority = make_valid_example()["authority"].copy()
        authority["auditLevel"] = "very-detailed"
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(authority=authority))

    def test_audit_levels_pass(self) -> None:
        for level in ("full", "summary", "minimal"):
            authority = make_valid_example()["authority"].copy()
            authority["auditLevel"] = level
            validate_example(make_valid_example(authority=authority))

    def test_artifact_pending_review_admission_status(self) -> None:
        artifact = {
            "artifactId": "artifact-001",
            "artifactType": "patch",
            "admissionStatus": "pending-review",
            "ref": "artifacts/patch/test.diff",
            "createdAt": "2026-05-06T19:00:00Z",
            "admittedAt": None,
            "admittedBy": None,
        }
        validate_example(make_valid_example(artifacts=[artifact]))

    def test_artifact_invalid_type_rejected(self) -> None:
        artifact = {"artifactId": "artifact-001", "artifactType": "unknown-type", "admissionStatus": "pending-review", "ref": "x", "createdAt": "2026-05-06T19:00:00Z", "admittedAt": None, "admittedBy": None}
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(artifacts=[artifact]))

    def test_artifact_invalid_admission_status_rejected(self) -> None:
        artifact = {"artifactId": "artifact-001", "artifactType": "patch", "admissionStatus": "activated", "ref": "x", "createdAt": "2026-05-06T19:00:00Z", "admittedAt": None, "admittedBy": None}
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(artifacts=[artifact]))

    def test_policy_gate_deny_allowed(self) -> None:
        gate = {"evaluated": True, "result": "deny", "policyRef": None, "evaluatedAt": None, "reason": "policy block"}
        validate_example(make_valid_example(policyGate=gate))

    def test_policy_gate_invalid_result_rejected(self) -> None:
        gate = {"evaluated": True, "result": "unknown", "policyRef": None, "evaluatedAt": None, "reason": None}
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(policyGate=gate))

    def test_negative_retry_count_rejected(self) -> None:
        lifecycle = make_valid_example()["lifecycle"].copy()
        lifecycle["retryCount"] = -1
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(lifecycle=lifecycle))

    def test_task_fields_validated(self) -> None:
        task = {"taskId": "task-001", "taskType": "read-context", "status": "completed", "startedAt": None, "completedAt": None, "inputRef": None, "outputRef": None, "notes": None}
        validate_example(make_valid_example(tasks=[task]))

    def test_task_invalid_status_rejected(self) -> None:
        task = {"taskId": "task-001", "taskType": "read-context", "status": "not-a-status", "startedAt": None, "completedAt": None, "inputRef": None, "outputRef": None, "notes": None}
        with pytest.raises(SystemExit):
            validate_example(make_valid_example(tasks=[task]))
