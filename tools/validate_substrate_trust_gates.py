#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "substrate-trust-gate.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "substrate-trust"

FAIL_CLOSED_DIAGNOSES = {"unsafe", "unknown"}
FAIL_CLOSED_FRESHNESS = {"expired", "missing"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    diagnosis = data.get("diagnosis_status")
    freshness = data.get("report_freshness")
    decision = data.get("gate_decision")

    # unsafe or unknown diagnosis must fail closed
    if diagnosis in FAIL_CLOSED_DIAGNOSES and decision not in ("fail_closed", "deny"):
        problems.append(f"diagnosis_status={diagnosis} requires gate_decision=fail_closed or deny")

    # expired or missing report must fail closed
    if freshness in FAIL_CLOSED_FRESHNESS and decision not in ("fail_closed", "deny"):
        problems.append(f"report_freshness={freshness} requires gate_decision=fail_closed or deny")

    # allow_degraded requires degraded_mode_authorization_ref
    if decision == "allow_degraded" and not data.get("degraded_mode_authorization_ref"):
        problems.append("allow_degraded requires degraded_mode_authorization_ref")

    # secure_lane must fail closed if secure_lane_redaction_required=true + fail_closed not set
    if data.get("substrate_type") == "secure_lane" and data.get("secure_lane_redaction_required") and decision == "allow":
        problems.append("secure_lane with secure_lane_redaction_required=true must not be allow; use allow_degraded or fail_closed")

    # attestation required but no ref when allowing
    if data.get("attestation_required") and decision in ("allow", "allow_degraded") and not data.get("attestation_ref"):
        problems.append("attestation_required=true with allow/allow_degraded requires attestation_ref")

    # non_claims required
    if not data.get("non_claims"):
        problems.append("non_claims must not be empty")

    return problems


def validate_file(path: Path, schema: dict[str, Any]) -> list[str]:
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"parse error: {exc}"]
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        return [f"schema: {exc.message}"]
    return check_policy_gates(data)


def main() -> int:
    schema = load_json(SCHEMA)
    failed = False

    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid substrate-trust fixtures")

    for path in valids:
        problems = validate_file(path, schema)
        if problems:
            print(f"FAIL (valid): {path.name}")
            for p in problems:
                print(f"  - {p}")
            failed = True
        else:
            print(f"ok: {path.name}")

    rejects = sorted(FIXTURES.glob("reject.*.json"))
    if not rejects:
        raise SystemExit("missing reject substrate-trust fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": substrate trust gates — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
