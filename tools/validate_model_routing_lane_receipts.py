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
SCHEMA = ROOT / "schemas" / "model-routing-lane-decision-receipt.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "model-routing"

HIGH_LANES = {"high_end", "pro"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    selected = data.get("selected_lane")
    outcome = data.get("lane_decision_outcome")
    stage = data.get("chain_stage")

    # high-end/pro without escalation receipt is denied
    if selected in HIGH_LANES and outcome not in ("denied", "deferred"):
        if not data.get("escalation_receipt_ref"):
            problems.append(f"selected_lane={selected} requires escalation_receipt_ref unless denied/deferred")
        if data.get("de_escalation_required_after_stage") is None:
            problems.append(f"selected_lane={selected} requires de_escalation_required_after_stage")

    # denied outcome: selected_lane should not be high-end (de-escalate to no_model)
    if outcome == "denied" and selected in HIGH_LANES:
        problems.append("denied outcome should de-escalate selected_lane to no_model or lightweight")

    # verification stage must default to no_model; model_primary not allowed
    if stage == "verification":
        vm = data.get("verification_mode")
        if vm == "model_primary":
            problems.append("verification stage must not use model_primary")
        if selected not in ("no_model", "lightweight"):
            # warn only if verification_mode is explicitly model_primary or not mechanical
            if vm and vm != "mechanical_tools_only":
                problems.append("verification stage should use mechanical_tools_only or no_model lane")

    # no raw prompts: prompt_evidence_policy must never be absent
    if not data.get("prompt_evidence_policy"):
        problems.append("prompt_evidence_policy is required")

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
        raise SystemExit("missing valid model-routing fixtures")

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
        raise SystemExit("missing reject model-routing fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": model-routing lane receipts — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
