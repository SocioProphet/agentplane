#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALID_FIXTURES = [
    ROOT / "tests" / "fixtures" / "sandbox" / "runtime-certification.runtime-observed.valid.json",
    ROOT / "tests" / "fixtures" / "sandbox" / "runtime-certification.runtime-certified.valid.json",
]
INVALID_FIXTURES = [
    ROOT / "tests" / "fixtures" / "sandbox" / "runtime-certification.certified-with-gaps.invalid.json",
]
ORDER = [
    "contract_only",
    "runtime_observed",
    "teardown_verified",
    "leak_check_verified",
    "runtime_certified",
]
REQUIRED_EVIDENCE = {
    "runtime_observed": ["contract_ref", "runtime_observation_ref"],
    "teardown_verified": ["contract_ref", "runtime_observation_ref", "teardown_ref"],
    "leak_check_verified": ["contract_ref", "runtime_observation_ref", "teardown_ref", "leak_check_ref"],
    "runtime_certified": ["contract_ref", "runtime_observation_ref", "teardown_ref", "leak_check_ref", "certification_receipt_ref"],
}


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object: {path}")
    return data


def validate(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    current = data.get("current_state")
    chain = data.get("promotion_chain", [])
    refs = data.get("evidence_refs", {})
    gaps = data.get("blocking_gaps", [])
    effects = data.get("effects", {})
    authority = data.get("authority", {})

    if data.get("schema_version") != "0.1":
        problems.append("schema_version must be 0.1")
    if not str(data.get("state_ref", "")).startswith("agentplane:runtime-certification-state:"):
        problems.append("state_ref must be an AgentPlane runtime certification state ref")
    if not str(data.get("runtime_run_ref", "")).startswith("agentplane:runtime-sandbox-run:"):
        problems.append("runtime_run_ref must reference an AgentPlane runtime sandbox run")
    if current not in ORDER:
        problems.append("current_state is invalid")
    if not isinstance(chain, list) or not chain:
        problems.append("promotion_chain must be non-empty")
    if not isinstance(refs, dict):
        problems.append("evidence_refs must be an object")
    if not isinstance(gaps, list):
        problems.append("blocking_gaps must be a list")

    if authority.get("state_authority") != "AgentPlane":
        problems.append("state_authority must be AgentPlane")
    if authority.get("execution_authority") != "AgentPlane":
        problems.append("execution_authority must be AgentPlane")
    if authority.get("certification_authority") != "AgentPlane":
        problems.append("certification_authority must be AgentPlane")

    seen_states: list[str] = []
    for item in chain if isinstance(chain, list) else []:
        state = item.get("state") if isinstance(item, dict) else None
        if state not in ORDER:
            problems.append(f"invalid chain state: {state}")
            continue
        seen_states.append(state)
        if not item.get("entered_at"):
            problems.append(f"{state} missing entered_at")
        if "promotion_allowed" not in item or not isinstance(item.get("promotion_allowed"), bool):
            problems.append(f"{state} missing boolean promotion_allowed")
        if not isinstance(item.get("blocked_by", []), list):
            problems.append(f"{state} blocked_by must be a list")

    if current in ORDER and seen_states:
        current_index = ORDER.index(current)
        expected_prefix = ORDER[: current_index + 1]
        if current == "runtime_observed":
            expected_prefix = ["contract_only", "runtime_observed"]
        if current == "runtime_certified":
            expected_prefix = ORDER
        if seen_states != expected_prefix:
            problems.append(f"promotion_chain must equal {expected_prefix} for {current}; got {seen_states}")

    if isinstance(refs, dict) and current in REQUIRED_EVIDENCE:
        for key in REQUIRED_EVIDENCE[current]:
            if not refs.get(key):
                problems.append(f"{current} requires evidence_refs.{key}")

    certified = effects.get("runtime_parity_certified") is True
    if current == "runtime_certified":
        if gaps:
            problems.append("runtime_certified cannot have blocking_gaps")
        for key in REQUIRED_EVIDENCE["runtime_certified"]:
            if not refs.get(key):
                problems.append(f"runtime_certified requires evidence_refs.{key}")
        if not certified:
            problems.append("runtime_certified must set runtime_parity_certified true")
        if effects.get("promotion_allowed") is not True:
            problems.append("runtime_certified must allow promotion")
        if effects.get("human_review_required") is not False:
            problems.append("runtime_certified must not require human review")
    else:
        if certified:
            problems.append("non-certified current_state must not set runtime_parity_certified true")
        if effects.get("autonomy_allowed") is True:
            problems.append("non-certified current_state must not allow autonomy")
        if effects.get("promotion_allowed") is True:
            problems.append("non-certified current_state must not allow promotion")

    if certified and gaps:
        problems.append("runtime parity certification cannot coexist with blocking gaps")
    if certified and (not refs.get("teardown_ref") or not refs.get("leak_check_ref")):
        problems.append("runtime parity certification requires teardown and leak-check refs")

    if not isinstance(data.get("non_claims"), list) or not data.get("non_claims"):
        problems.append("non_claims must be non-empty")
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
        "validator": "agentplane.runtime-certification-state.validator.v1",
        "passed": not failed,
        "results": results,
        "non_claims": [
            "Validator checks runtime certification state semantics only.",
            "Validator does not execute infrastructure.",
            "Validator does not replace downstream policy admission."
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(("PASS" if not failed else "FAIL") + ": runtime certification state fixtures")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
