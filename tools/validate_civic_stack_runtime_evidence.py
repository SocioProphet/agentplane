#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "civic-stack-run-capsule.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "civic-stack"

ALLOWED_POLICY_OUTCOMES = {"allow", "allow_with_constraints", "deny", "escalate"}
ALLOWED_DISPATCH_STATUSES = {"dispatched", "blocked", "deferred", "completed"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    outcome = data.get("policy_decision_outcome")
    if outcome and outcome not in ALLOWED_POLICY_OUTCOMES:
        problems.append(f"policy_decision_outcome invalid: {outcome}")

    # deny outcome: tool_grants must be empty and all dispatches must be blocked
    if outcome == "deny":
        grants = data.get("tool_grants", [])
        if grants:
            problems.append("deny policy_decision_outcome must have no tool_grants")
        dispatches = data.get("action_dispatch_records", [])
        non_blocked = [d for d in dispatches if d.get("dispatch_status") != "blocked"]
        if non_blocked:
            problems.append("deny policy_decision_outcome requires all dispatches blocked")

    # blocked dispatches must have defeater_reason
    for dispatch in data.get("action_dispatch_records", []):
        if dispatch.get("dispatch_status") == "blocked" and not dispatch.get("defeater_reason"):
            problems.append(f"blocked dispatch {dispatch.get('dispatch_id')} requires defeater_reason")

    # rationalgrl_trace: blocked tasks must have defeater_reason
    trace = data.get("rationalgrl_trace", {})
    for task in trace.get("tasks_executed", []):
        if task.get("execution_status") == "blocked" and not task.get("defeater_reason"):
            problems.append(f"blocked task {task.get('task_ref')} in rationalgrl_trace requires defeater_reason")

    # hellgraph_evidence_refs required and non-empty (belt-and-suspenders on schema minItems)
    hg_refs = data.get("hellgraph_evidence_refs", [])
    if not hg_refs:
        problems.append("hellgraph_evidence_refs must not be empty")

    # provenance_refs required and non-empty
    prov_refs = data.get("provenance_refs", [])
    if not prov_refs:
        problems.append("provenance_refs must not be empty")

    # oac_compiler_invocation: failure status should have no artifact_emission_refs
    oac = data.get("oac_compiler_invocation")
    if oac and oac.get("invocation_status") == "failure":
        if oac.get("artifact_emission_refs"):
            problems.append("oac_compiler_invocation failure must not have artifact_emission_refs")

    return problems


def validate_file(path: Path, schema: dict[str, Any]) -> list[str]:
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"parse error: {exc}"]
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        return [f"schema: {exc.message}"]
    return check_policy_gates(data)


def main() -> int:
    schema = load_json(SCHEMA)
    failed = False

    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid civic-stack fixtures")

    for path in valids:
        problems = validate_file(path, schema)
        if problems:
            print(f"FAIL (valid): {path.name}")
            for p in problems:
                print(f"  - {p}")
            failed = True
        else:
            print(f"ok: {path.name}")

    rejects = sorted(FIXTURES.glob("reject.*.json"))
    if not rejects:
        raise SystemExit("missing reject civic-stack fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": civic-stack runtime evidence — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
