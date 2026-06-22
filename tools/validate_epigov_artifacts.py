#!/usr/bin/env python3
"""Validate Epistemic Governance bundle artifacts.

Checks HygieneRunArtifact and CountertestRunArtifact schema conformance.
Policy gates:
- sociosphere_protocol_ref must be protocol/epistemic-governance/v1
- ruleset_hash and input_hash must match sha256:<64-hex>
- Tampered input (replay_verified=false) must fail
- CountertestRunArtifact must reference a hygiene_run_ref
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
HYGIENE_SCHEMA = json.loads(
    (ROOT / "schemas" / "hygiene-run-artifact.schema.json").read_text()
)
COUNTERTEST_SCHEMA = json.loads(
    (ROOT / "schemas" / "countertest-run-artifact.schema.json").read_text()
)

HASH_RE = re.compile(r"^sha256:[A-Fa-f0-9]{64}$")
EPIGOV_PROTOCOL = "protocol/epistemic-governance/v1"

EXAMPLE_PATHS = [
    ROOT / "examples" / "receipts" / "epigov-strawman-smoke" / "hygiene-run-artifact.example.json",
    ROOT / "examples" / "receipts" / "epigov-strawman-smoke" / "countertest-run-artifact.example.json",
]

errors: list[str] = []
results: list[bool] = []


def ok(label: str) -> None:
    print(f"PASS {label}")
    results.append(True)


def fail(label: str, reason: str) -> None:
    errors.append(f"FAIL {label}: {reason}")
    results.append(False)


def detect_schema(data: dict) -> tuple[str, dict] | None:
    kind = data.get("kind")
    if kind == "HygieneRunArtifact":
        return kind, HYGIENE_SCHEMA
    if kind == "CountertestRunArtifact":
        return kind, COUNTERTEST_SCHEMA
    return None


def policy_gate_errors(data: dict, kind: str) -> list[str]:
    errs = []
    proto = data.get("sociosphere_protocol_ref", "")
    if proto != EPIGOV_PROTOCOL:
        errs.append(f"sociosphere_protocol_ref must be {EPIGOV_PROTOCOL!r}, got {proto!r}")
    for field in ("ruleset_hash", "input_hash"):
        v = data.get(field, "")
        if v and not HASH_RE.match(v):
            errs.append(f"{field} must match sha256:<64-hex>")
    if data.get("replay_verified") is False:
        errs.append("replay_verified=false — tampered input detected; run artifact is invalid")
    if kind == "CountertestRunArtifact" and not data.get("hygiene_run_ref"):
        errs.append("CountertestRunArtifact requires hygiene_run_ref")
    return errs


for path in EXAMPLE_PATHS:
    label = path.name
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, FileNotFoundError) as e:
        fail(f"load {label}", str(e))
        continue

    ok(f"json-load {label}")

    detected = detect_schema(data)
    if detected is None:
        fail(f"kind {label}", "unknown artifact kind")
        continue

    kind, schema = detected
    v = jsonschema.Draft202012Validator(schema)
    schema_errs = list(v.iter_errors(data))
    policy_errs = policy_gate_errors(data, kind)

    for e in schema_errs:
        fail(f"schema {label}", e.message)
    for e in policy_errs:
        fail(f"policy-gate {label}", e)
    if not schema_errs and not policy_errs:
        ok(f"valid {label} ({kind})")

# Also validate bundle.json files parse as valid JSON
for bundle_dir in ["epigov-hygiene-detector-smoke", "epigov-countertest-smoke", "epigov-policy-backtest"]:
    bundle_path = ROOT / "bundles" / bundle_dir / "bundle.json"
    try:
        data = json.loads(bundle_path.read_text())
        if data.get("kind") != "Bundle":
            fail(f"bundle-kind {bundle_dir}", "kind must be Bundle")
        else:
            ok(f"bundle-json {bundle_dir}")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        fail(f"bundle-load {bundle_dir}", str(e))

passed = sum(results)
if errors:
    print(file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    print(f"\n{passed} passed, {len(errors)} failed", file=sys.stderr)
    sys.exit(1)

print(f"\n{passed} epigov-artifacts checks passed")
