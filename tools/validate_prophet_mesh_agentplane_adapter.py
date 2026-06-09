#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "contracts/prophet-mesh/prophet-mesh-agentplane-adapter.v0.1.json"

REQUIRED_TOP = {
    "schema_version",
    "kind",
    "source_repo",
    "target_repo",
    "release_channel",
    "adapter_mode",
    "source_artifacts",
    "required_runtime_sections",
    "required_agentplane_artifacts",
    "request_projection",
    "artifact_expectation",
    "private_preview_invariants",
    "non_claims",
}

REQUIRED_SECTIONS = {"router_decision", "choir_plan", "conductor_response", "execution_trace", "validation"}
REQUIRED_ARTIFACTS = {"validation_artifact", "placement_decision", "run_artifact", "replay_artifact"}
REQUIRED_CONTROLS = {"identity", "policy", "evidence", "attestation", "revocation", "audit", "tenant_isolation"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("fixture must be a JSON object")
    return data


def non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    missing = REQUIRED_TOP - set(data)
    if missing:
        problems.append("missing top-level fields: " + ", ".join(sorted(missing)))

    if data.get("kind") != "prophet_mesh_agentplane_adapter_contract":
        problems.append("kind must be prophet_mesh_agentplane_adapter_contract")
    if data.get("source_repo") != "SocioProphet/prophet-mesh":
        problems.append("source_repo must be SocioProphet/prophet-mesh")
    if data.get("target_repo") != "SocioProphet/agentplane":
        problems.append("target_repo must be SocioProphet/agentplane")
    if data.get("release_channel") != "private_preview":
        problems.append("release_channel must be private_preview")
    if data.get("adapter_mode") != "dry_run_receipt_preview":
        problems.append("adapter_mode must be dry_run_receipt_preview")

    sections = {str(item) for item in data.get("required_runtime_sections", [])}
    missing_sections = REQUIRED_SECTIONS - sections
    if missing_sections:
        problems.append("required_runtime_sections missing: " + ", ".join(sorted(missing_sections)))

    artifacts = {str(item) for item in data.get("required_agentplane_artifacts", [])}
    missing_artifacts = REQUIRED_ARTIFACTS - artifacts
    if missing_artifacts:
        problems.append("required_agentplane_artifacts missing: " + ", ".join(sorted(missing_artifacts)))

    projection = data.get("request_projection", {})
    if not isinstance(projection, dict):
        problems.append("request_projection must be an object")
        projection = {}

    if projection.get("task") == "email_reply" and projection.get("operator_review_required") is not True:
        problems.append("email_reply projection must require operator review")
    if projection.get("projection_mode") != "receipt_only":
        problems.append("projection_mode must be receipt_only")
    if projection.get("effect_enabled") is not False:
        problems.append("effect_enabled must be false")
    if projection.get("workspace_write_enabled") is not False:
        problems.append("workspace_write_enabled must be false")
    if not isinstance(projection.get("memory_scope"), str) or not projection.get("memory_scope"):
        problems.append("memory_scope must be explicit")

    for key in ("approval_refs", "evidence_refs", "audit_refs"):
        if not non_empty_list(projection.get(key)):
            problems.append(f"{key} must be a non-empty list")

    controls = projection.get("controls", {})
    if not isinstance(controls, dict):
        problems.append("controls must be an object")
    else:
        missing_controls = [key for key in sorted(REQUIRED_CONTROLS) if controls.get(key) is not True]
        if missing_controls:
            problems.append("controls missing true values: " + ", ".join(missing_controls))

    expectation = data.get("artifact_expectation", {})
    if not isinstance(expectation, dict):
        problems.append("artifact_expectation must be an object")
        expectation = {}

    for key in (
        "validation_artifact_required",
        "placement_decision_required",
        "run_artifact_required",
        "replay_artifact_required",
    ):
        if expectation.get(key) is not True:
            problems.append(f"artifact_expectation.{key} must be true")

    if expectation.get("run_artifact_status") != "not_run_receipt_only":
        problems.append("run_artifact_status must be not_run_receipt_only")
    if expectation.get("replay_artifact_mode") != "metadata_only":
        problems.append("replay_artifact_mode must be metadata_only")
    if expectation.get("effect_receipts_required") is not False:
        problems.append("effect_receipts_required must be false")
    if expectation.get("executor_required") is not False:
        problems.append("executor_required must be false")

    return problems


def main() -> int:
    try:
        data = load_json(FIXTURE)
    except Exception as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2

    problems = validate(data)
    report = {
        "validator": "agentplane.prophet-mesh-agentplane-adapter.validator.v1",
        "passed": not problems,
        "problems": problems,
        "fixture": str(FIXTURE.relative_to(ROOT)),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(("PASS" if not problems else "FAIL") + ": Prophet Mesh AgentPlane adapter")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
