#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "tests" / "fixtures" / "sandbox"
VALID_FIXTURES = [
    SANDBOX / "runtime-sandbox-run.requested.valid.json",
    SANDBOX / "runtime-sandbox-run.allocated.valid.json",
    SANDBOX / "runtime-sandbox-run.failed.valid.json",
    SANDBOX / "runtime-sandbox-run.shared-receipt.valid.json",
    SANDBOX / "runtime-sandbox-run.teardown.valid.json",
]
INVALID_FIXTURES = [
    SANDBOX / "runtime-sandbox-run.allocated.missing-leakcheck.invalid.json",
    SANDBOX / "runtime-sandbox-run.teardown.missing-evidence.invalid.json",
]
STATUSES = {"runtime_requested", "runtime_allocated", "runtime_failed", "runtime_teardown_complete"}
PARITY_LEVELS = {"contract_only", "runtime_observed"}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object: {path}")
    return data


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    status = data.get("runStatus")
    parity = data.get("runtimeParityLevel")
    evidence_refs = data.get("evidenceRefs", [])
    receipt_refs = data.get("receiptRefs", [])
    failure_codes = data.get("failureCodes", [])
    isolation = data.get("isolationRefs", {})

    if data.get("schemaVersion") != "0.1.0":
        problems.append("schemaVersion must be 0.1.0")
    if not str(data.get("runtimeRunId", "")).startswith("agentplane:runtime-sandbox-run:"):
        problems.append("runtimeRunId must be agentplane runtime sandbox run id")
    if not str(data.get("requestRef", "")).startswith("environment:validate-change-v2-request:"):
        problems.append("requestRef must reference validate_change v2 request")
    if data.get("executorPlane") != "AgentPlane":
        problems.append("executorPlane must be AgentPlane")
    if data.get("executionMode") != "runtime_contract":
        problems.append("executionMode must be runtime_contract")
    if parity not in PARITY_LEVELS:
        problems.append("runtimeParityLevel is invalid")
    if status not in STATUSES:
        problems.append("runStatus is invalid")
    if not str(data.get("environmentRef", "")).startswith("environment://"):
        problems.append("environmentRef must use environment://")
    if not str(data.get("baselineRef", "")).startswith("workspace://"):
        problems.append("baselineRef must use workspace://")
    if not isinstance(data.get("changedServiceRefs"), list):
        problems.append("changedServiceRefs must be a list")
    if not str(data.get("dependencyGraphRef", "")).startswith("dependency-graph://"):
        problems.append("dependencyGraphRef must use dependency-graph://")
    if not str(data.get("routingRef", "")).startswith("routing://"):
        problems.append("routingRef must use routing://")
    if not isinstance(isolation, dict):
        problems.append("isolationRefs must be an object")
    else:
        for key in ("network", "async", "stateful"):
            if not str(isolation.get(key, "")).startswith("isolation://"):
                problems.append(f"isolationRefs.{key} must use isolation://")
    if not isinstance(evidence_refs, list):
        problems.append("evidenceRefs must be a list")
    if not isinstance(receipt_refs, list):
        problems.append("receiptRefs must be a list")
    if not isinstance(failure_codes, list):
        problems.append("failureCodes must be a list")
    if any(not str(ref).startswith("evidence://") for ref in evidence_refs):
        problems.append("all evidence refs must use evidence://")
    if any(not str(ref).startswith("receipt://") for ref in receipt_refs):
        problems.append("all receipt refs must use receipt://")
    if data.get("teardownState") not in {"not_started", "teardown_complete", "teardown_failed"}:
        problems.append("teardownState is invalid")
    if not str(data.get("leakCheckRef", "")).startswith("leak-check://"):
        problems.append("leakCheckRef must use leak-check://")
    if not isinstance(data.get("nonClaims"), list) or not data.get("nonClaims"):
        problems.append("nonClaims must be non-empty")

    if status == "runtime_requested":
        if parity != "contract_only":
            problems.append("runtime_requested must remain contract_only")
        if evidence_refs or receipt_refs:
            problems.append("runtime_requested must not have evidence or receipts")
        if failure_codes:
            problems.append("runtime_requested must not have failure codes")
        if data.get("teardownState") != "not_started":
            problems.append("runtime_requested teardownState must be not_started")
    if status == "runtime_allocated":
        if parity != "runtime_observed":
            problems.append("runtime_allocated must be runtime_observed")
        if not evidence_refs:
            problems.append("runtime_allocated requires evidence refs")
        if not receipt_refs:
            problems.append("runtime_allocated requires receipt refs")
        if failure_codes:
            problems.append("runtime_allocated must not have failure codes")
        if data.get("teardownState") != "not_started":
            problems.append("runtime_allocated teardownState must be not_started")
    if status == "runtime_failed":
        if parity != "contract_only":
            problems.append("runtime_failed must remain contract_only")
        if not evidence_refs:
            problems.append("runtime_failed requires evidence refs")
        if not receipt_refs:
            problems.append("runtime_failed requires receipt refs")
        if "runtime_allocation_failed" not in failure_codes:
            problems.append("runtime_failed requires runtime_allocation_failed")
        if data.get("teardownState") != "teardown_failed":
            problems.append("runtime_failed teardownState must be teardown_failed")
    if status == "runtime_teardown_complete":
        if parity != "runtime_observed":
            problems.append("runtime_teardown_complete must be runtime_observed")
        if not evidence_refs:
            problems.append("runtime_teardown_complete requires evidence refs")
        if not receipt_refs:
            problems.append("runtime_teardown_complete requires receipt refs")
        if failure_codes:
            problems.append("runtime_teardown_complete must not have failure codes")
        if data.get("teardownState") != "teardown_complete":
            problems.append("runtime_teardown_complete teardownState must be teardown_complete")

    return problems


def main() -> int:
    failed = False
    results: dict[str, Any] = {"valid": {}, "invalid": {}}

    for path in VALID_FIXTURES:
        problems = validate(load(path))
        results["valid"][str(path.relative_to(ROOT))] = problems
        failed = failed or bool(problems)

    for path in INVALID_FIXTURES:
        problems = validate(load(path))
        if not problems:
            problems = ["expected invalid fixture to fail validation"]
            failed = True
        results["invalid"][str(path.relative_to(ROOT))] = problems

    report = {
        "validator": "agentplane.runtime-sandbox-run.validator.v1",
        "passed": not failed,
        "results": results,
        "non_claims": [
            "Validator checks runtime sandbox contract semantics only.",
            "Validator does not allocate live infrastructure.",
            "Validator does not certify Signadot runtime parity."
        ]
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(("PASS" if not failed else "FAIL") + ": runtime sandbox run fixtures")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
