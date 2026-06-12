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
SCHEMA = ROOT / "schemas" / "device-actuation-boundary-receipt.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "device-actuation"

HIGH_RISK_CLASSES = {
    "lock", "alarm", "camera", "vehicle", "payment",
    "identity_token", "health_relevant", "os_mutation", "irreversible_deletion"
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    cap_class = data.get("capability_class")
    action_class = data.get("action_class")
    status = data.get("proposal_status")

    # high_risk action_class must always be capability_class=high_risk
    if action_class in HIGH_RISK_CLASSES and cap_class != "high_risk":
        problems.append(f"action_class={action_class} requires capability_class=high_risk")

    # high_risk + approved/executed requires approval_ref + approval_authority_ref
    if cap_class == "high_risk" and status in ("approved", "executed"):
        if not data.get("approval_ref"):
            problems.append("high_risk approved/executed requires approval_ref")
        if not data.get("approval_authority_ref"):
            problems.append("high_risk approved/executed requires approval_authority_ref")

    # denied must have denial_reason
    if status == "denied" and not data.get("denial_reason"):
        problems.append("denied proposal_status requires denial_reason")

    # rolled_back requires rollback_artifact_ref
    if status == "rolled_back" and not data.get("rollback_artifact_ref"):
        problems.append("rolled_back requires rollback_artifact_ref")

    # no bypass: proposed status must not have policy_outcome=allow on high_risk
    if status == "proposed" and cap_class == "high_risk" and data.get("policy_outcome") == "allow":
        problems.append("high_risk proposed action must not have policy_outcome=allow; approval required first")

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
        raise SystemExit("missing valid device-actuation fixtures")

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
        raise SystemExit("missing reject device-actuation fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": device actuation boundary — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
