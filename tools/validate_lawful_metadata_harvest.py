#!/usr/bin/env python3
"""Validate LawfulMetadataHarvestRunArtifact fixtures.

Policy gates:
- no_live_network_harvest must be true
- promotion_decision.promotion_is_explicit must be true (promotion is never implied by harvest completion)
- token_loop_anomaly.detected=true invalidates replay — run must be rejected
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
SCHEMA_PATH = ROOT / "schemas" / "lawful-metadata-harvest-run-artifact.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "lawful-metadata-harvest"

SCHEMA = json.loads(SCHEMA_PATH.read_text())

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
    if not data.get("no_live_network_harvest"):
        errs.append("no_live_network_harvest must be true")
    pd = data.get("promotion_decision", {})
    if not pd.get("promotion_is_explicit"):
        errs.append("promotion_decision.promotion_is_explicit must be true")
    anomaly = data.get("token_loop_anomaly", {})
    if anomaly.get("detected") and anomaly.get("anomaly_type") != "none":
        errs.append(
            f"token_loop_anomaly detected ({anomaly.get('anomaly_type')}) — run artifact is invalid; replay is not trusted"
        )
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

print(f"\n{passed} lawful-metadata-harvest checks passed")
