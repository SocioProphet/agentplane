#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "receipts" / "health-ai-control-receipt.v0.1.schema.json"
FIXTURE = ROOT / "tests" / "fixtures" / "receipts" / "health-ai-control-receipt.planning-valid.json"

REQUIRED_BLOCKS = {
    "production_ready",
    "patient_care_action",
    "autonomous_clinical_action",
    "real_clinical_data_processing",
    "customer_facing_healthcare_claim",
    "protected_benchmark_reproduction",
}

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    errors: list[str] = []

    try:
        schema = load(SCHEMA)
        fixture = load(FIXTURE)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(fixture)
    except Exception as exc:
        print(f"ERR: Health AI control receipt schema validation failed: {exc}", file=sys.stderr)
        return 2

    control = fixture.get("control_decision", {})
    if control.get("state") != "planning_only":
        errors.append("control_decision.state must be planning_only")
    if control.get("production_ready") is not False:
        errors.append("production_ready must be false")

    missing_blocks = sorted(REQUIRED_BLOCKS - set(control.get("blocked_actions", [])))
    if missing_blocks:
        errors.append(f"missing blocked actions: {missing_blocks}")

    benchmark = fixture.get("benchmark_boundary", {})
    for key in ("protected_examples_reproduced", "answer_keys_reproduced", "canary_reproduced"):
        if benchmark.get(key) is not False:
            errors.append(f"benchmark_boundary.{key} must be false")

    clinical = fixture.get("clinical_boundary", {})
    for key in (
        "patient_care_action",
        "autonomous_clinical_action",
        "real_clinical_data_processing",
        "customer_facing_healthcare_claim",
    ):
        if clinical.get(key) is not False:
            errors.append(f"clinical_boundary.{key} must be false")

    required_refs = [
        "prophet-core-contracts:make validate-health-ai-contracts",
        "sherlock-search:make validate-health-ai-search-packets",
        "sociosphere:python3 tools/validate_health_ai_readiness.py",
    ]
    refs = fixture.get("validation_refs", [])
    for ref in required_refs:
        if ref not in refs:
            errors.append(f"missing validation ref: {ref}")

    if errors:
        print("ERR: Health AI control receipt validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    print("Health AI control receipt validates as planning_only.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
