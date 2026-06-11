#!/usr/bin/env python3
"""Validate ReasoningFailureTrace fixtures against schema."""
import json
import pathlib
import sys

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed", file=sys.stderr)
    sys.exit(1)

ROOT = pathlib.Path(__file__).parent.parent
SCHEMA = json.loads((ROOT / "schemas" / "reasoning-failure-trace.schema.v0.1.json").read_text())
FIXTURES = ROOT / "tests" / "fixtures" / "reasoning-failure-traces"

validator = jsonschema.Draft202012Validator(SCHEMA)
errors = []

for fixture in sorted(FIXTURES.glob("*.json")):
    doc = json.loads(fixture.read_text())
    errs = list(validator.iter_errors(doc))
    if errs:
        for e in errs:
            errors.append(f"FAIL {fixture.name}: {e.message}")
    else:
        print(f"PASS {fixture.name}")

if errors:
    print(file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    sys.exit(1)

total = len(list(FIXTURES.glob("*.json")))
print(f"\n{total} fixtures passed")
