#!/usr/bin/env python3
"""Validate AuthorityDependencyEvidence examples against schema."""
import json
import pathlib
import sys

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed", file=sys.stderr)
    sys.exit(1)

ROOT = pathlib.Path(__file__).parent.parent
SCHEMA = json.loads((ROOT / "schemas" / "authority-dependency-evidence.schema.v0.1.json").read_text())
EXAMPLES = ROOT / "examples" / "authority-dependency-evidence"

validator = jsonschema.Draft202012Validator(SCHEMA)
errors = []

for example in sorted(EXAMPLES.glob("*.json")):
    doc = json.loads(example.read_text())
    errs = list(validator.iter_errors(doc))
    if errs:
        for e in errs:
            errors.append(f"FAIL {example.name}: {e.message}")
    else:
        print(f"PASS {example.name}")

if errors:
    print(file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    sys.exit(1)

print(f"\n{len(list(EXAMPLES.glob('*.json')))} examples passed")
