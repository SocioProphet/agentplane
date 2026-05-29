#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = [
    ROOT / "tests" / "fixtures" / "sandbox" / "sandbox-run.requested.valid.json",
    ROOT / "tests" / "fixtures" / "sandbox" / "sandbox-run.observed.valid.json",
    ROOT / "tests" / "fixtures" / "sandbox" / "sandbox-run.failed.valid.json",
]
INVALID_FIXTURES = [
    ROOT / "tests" / "fixtures" / "sandbox" / "sandbox-run.observed.missing-evidence.invalid.json",
]
STATUSES = {"sandbox_requested", "sandbox_observed", "sandbox_failed"}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"fixture must be an object: {path}")
    return data


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    status = data.get("runStatus")
    evidence_refs = data.get("evidenceRefs", [])
    receipt_refs = data.get("receiptRefs", [])
    failure_codes = data.get("failureCodes", [])

    if data.get("schemaVersion") != "0.1.0":
        problems.append("schemaVersion must be 0.1.0")
    if not str(data.get("sandboxRunId", "")).startswith("agentplane:sandbox-run:"):
        problems.append("sandboxRunId must start with agentplane:sandbox-run:")
    if not str(data.get("requestRef", "")).startswith("environment:validate-change-v2-request:"):
        problems.append("requestRef must reference validate_change v2 request")
    if data.get("executorPlane") != "AgentPlane":
        problems.append("executorPlane must be AgentPlane")
    if data.get("executionMode") != "synthetic_fixture":
        problems.append("executionMode must be synthetic_fixture")
    if status not in STATUSES:
        problems.append(f"invalid runStatus: {status}")
    if not str(data.get("baselineRef", "")).startswith("workspace://"):
        problems.append("baselineRef must start with workspace://")
    if not isinstance(data.get("changedServiceRefs"), list):
        problems.append("changedServiceRefs must be a list")
    if data.get("routingMode") not in {"not_configured", "synthetic_no_network"}:
        problems.append("routingMode is invalid")
    if data.get("asyncIsolationMode") not in {"not_configured", "synthetic_no_network"}:
        problems.append("asyncIsolationMode is invalid")
    if data.get("statefulResourceMode") not in {"not_configured", "synthetic_no_network"}:
        problems.append("statefulResourceMode is invalid")
    if not isinstance(evidence_refs, list):
        problems.append("evidenceRefs must be a list")
    if not isinstance(receipt_refs, list):
        problems.append("receiptRefs must be a list")
    if not isinstance(failure_codes, list):
        problems.append("failureCodes must be a list")
    if not isinstance(data.get("nonClaims"), list) or not data.get("nonClaims"):
        problems.append("nonClaims must be a non-empty list")

    if status == "sandbox_requested":
        if evidence_refs:
            problems.append("sandbox_requested must not have evidenceRefs")
        if receipt_refs:
            problems.append("sandbox_requested must not have receiptRefs")
        if failure_codes:
            problems.append("sandbox_requested must not have failureCodes")
    if status == "sandbox_observed":
        if not evidence_refs:
            problems.append("sandbox_observed requires evidenceRefs")
        if not receipt_refs:
            problems.append("sandbox_observed requires receiptRefs")
        if failure_codes:
            problems.append("sandbox_observed must not have failureCodes")
    if status == "sandbox_failed":
        if not evidence_refs:
            problems.append("sandbox_failed requires evidenceRefs")
        if not receipt_refs:
            problems.append("sandbox_failed requires receiptRefs")
        if "synthetic_validation_failed" not in failure_codes:
            problems.append("sandbox_failed requires synthetic_validation_failed")

    return problems


def main() -> int:
    results: dict[str, Any] = {"valid": {}, "invalid": {}}
    failed = False

    for path in FIXTURES:
        problems = validate(load(path))
        results["valid"][str(path.relative_to(ROOT))] = problems
        failed = failed or bool(problems)

    for path in INVALID_FIXTURES:
        problems = validate(load(path))
        results["invalid"][str(path.relative_to(ROOT))] = problems
        if not problems:
            failed = True
            results["invalid"][str(path.relative_to(ROOT))] = ["expected invalid fixture to fail validation"]

    report = {
        "validator": "agentplane.sandbox-run.synthetic.validator.v1",
        "passed": not failed,
        "results": results,
        "non_claims": [
            "Validator does not execute live sandbox infrastructure.",
            "Validator does not certify Signadot-style runtime parity.",
            "Validator checks synthetic SandboxRun contract semantics only."
        ]
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(("PASS" if not failed else "FAIL") + ": synthetic SandboxRun fixtures")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
