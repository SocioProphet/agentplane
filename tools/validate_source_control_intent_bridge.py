#!/usr/bin/env python3
"""Validate SourceControlIntentBridgeArtifact fixtures.

Validates fixtures against source-control-intent-bridge.schema.v0.1.json.
Enforces:
- AgentPlane admission ref is non-empty for admitted/replayed status
- runtime_ready must be false (scaffold baseline != runtime readiness)
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
SCHEMA_PATH = ROOT / "schemas" / "source-control-intent-bridge.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "source-control-intent"

SCHEMA = json.loads(SCHEMA_PATH.read_text())

errors: list[str] = []
results: list[bool] = []


def ok(label: str) -> None:
    print(f"PASS {label}")
    results.append(True)


def fail(label: str, reason: str) -> None:
    errors.append(f"FAIL {label}: {reason}")
    results.append(False)


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

    # Extra gate: runtime_ready must be false
    runtime_err = None
    if data.get("runtime_ready") is True:
        runtime_err = "runtime_ready must be false — scaffold baseline does not imply runtime readiness"

    has_errors = bool(schema_errs) or bool(runtime_err)

    if is_reject:
        if has_errors:
            ok(f"reject-expected {label}")
        else:
            fail(f"reject-fixture {label}", "expected failure but fixture appears valid")
    else:
        if schema_errs:
            for e in schema_errs:
                fail(f"schema {label}", e.message)
        elif runtime_err:
            fail(f"runtime-ready-gate {label}", runtime_err)
        else:
            ok(f"schema {label}")

passed = sum(results)
if errors:
    print(file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    print(f"\n{passed} passed, {len(errors)} failed", file=sys.stderr)
    sys.exit(1)

print(f"\n{passed} source-control-intent-bridge checks passed")
