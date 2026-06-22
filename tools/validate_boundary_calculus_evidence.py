#!/usr/bin/env python3
"""Validate BoundaryCalculusEvidenceEnvelope fixtures.

Policy gates (beyond schema validation):
- claim_status=metaphor requires load_bearing=false
- confirmed/load_bearing_assertion status requires promotion_gate != none_required
- policy_result=escalate requires security_escalation_ref
- attribution_source present requires attribution_discriminating_evidence_refs (minItems 1)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "boundary-calculus-evidence-envelope.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "boundary-calculus"

SCHEMA = json.loads(SCHEMA_PATH.read_text())

STRONG_CLAIM_STATUSES = {"confirmed", "load_bearing_assertion"}

errors: list[str] = []
results: list[bool] = []


def ok(label: str) -> None:
    print(f"PASS {label}")
    results.append(True)


def fail(label: str, reason: str) -> None:
    errors.append(f"FAIL {label}: {reason}")
    results.append(False)


def policy_gate_errors(data: dict) -> list[str]:
    errs = []
    status = data.get("claim_status")
    load_bearing = data.get("load_bearing")
    promotion_gate = data.get("promotion_gate")
    policy_result = data.get("policy_result")
    attribution = data.get("attribution_source")
    attribution_ev = data.get("attribution_discriminating_evidence_refs", [])

    # metaphor + load_bearing check (also in schema via conditional, belt-and-suspenders)
    if status == "metaphor" and load_bearing is True:
        errs.append("claim_status=metaphor requires load_bearing=false")

    # strong claims require a real promotion gate
    if status in STRONG_CLAIM_STATUSES and promotion_gate == "none_required":
        errs.append(f"claim_status={status} requires promotion_gate != none_required")

    # escalation requires escalation ref
    if policy_result == "escalate" and not data.get("security_escalation_ref"):
        errs.append("policy_result=escalate requires security_escalation_ref")

    # attribution requires discriminating evidence
    if attribution and not attribution_ev:
        errs.append("attribution_source present requires attribution_discriminating_evidence_refs (minItems 1)")

    return errs


for path in sorted(FIXTURES.glob("*.json")):
    is_reject = path.name.startswith("reject_")
    label = path.name

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"json-parse {label}", str(e))
        continue

    ok(f"json-parse {label}")

    v = jsonschema.Draft202012Validator(SCHEMA)
    schema_errs = list(v.iter_errors(data))
    policy_errs = policy_gate_errors(data)
    has_errors = bool(schema_errs) or bool(policy_errs)

    if is_reject:
        if has_errors:
            ok(f"reject-expected {label}")
        else:
            fail(f"reject-fixture {label}", "expected failure but fixture appears valid")
    else:
        for e in schema_errs:
            fail(f"schema {label}", e.message)
        for e in policy_errs:
            fail(f"policy-gate {label}", e)
        if not schema_errs and not policy_errs:
            ok(f"valid {label}")

passed = sum(results)
if errors:
    print(file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    print(f"\n{passed} passed, {len(errors)} failed", file=sys.stderr)
    sys.exit(1)

print(f"\n{passed} boundary-calculus-evidence checks passed")
