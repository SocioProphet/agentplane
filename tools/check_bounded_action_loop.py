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
SCHEMA = ROOT / "schemas" / "bounded-action-loop.v0.schema.json"
FIXTURES = ROOT / "tests" / "fixtures" / "bounded-action-loop"

INTERVENTION_STATUSES = {"blocked", "modified", "escalated"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_data(data: dict[str, Any]) -> None:
    proposal = data["action_proposal"]
    trace = data["runtime_trace"]
    outcome = data["outcome_record"]
    policy_ref = data["policy_decision_ref"]

    if trace["proposal_ref"] != proposal["proposal_id"]:
        raise ValueError("trace proposal ref mismatch")
    if outcome["proposal_ref"] != proposal["proposal_id"]:
        raise ValueError("outcome proposal ref mismatch")
    if trace["policy_decision_ref"] != policy_ref:
        raise ValueError("trace policy ref mismatch")
    if outcome["policy_decision_ref"] != policy_ref:
        raise ValueError("outcome policy ref mismatch")
    if not proposal["evidence_refs"]:
        raise ValueError("proposal evidence refs required")
    if proposal["risk_class"] != "low" and trace["trace_status"] == "recorded":
        raise ValueError("recorded trace requires low risk in v0")
    # Runtime trace must always be present and consistent with outcome
    if trace["trace_status"] != outcome["result"]:
        raise ValueError("trace_status and outcome result must match")
    # Intervention outcomes (blocked/modified/escalated) must have audit_ref
    if outcome["result"] in INTERVENTION_STATUSES and not outcome.get("audit_ref"):
        raise ValueError(f"intervention outcome result={outcome['result']} requires audit_ref")


def validate_file(path: Path, schema: dict[str, Any]) -> None:
    data = load_json(path)
    jsonschema.validate(data, schema)
    check_data(data)


def main() -> int:
    schema = load_json(SCHEMA)
    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid bounded-action-loop fixtures")
    for path in valids:
        validate_file(path, schema)
    invalids = sorted(FIXTURES.glob("invalid.*.json"))
    if not invalids:
        raise SystemExit("missing invalid bounded-action-loop fixtures")
    unexpected = []
    for path in invalids:
        try:
            validate_file(path, schema)
        except Exception:
            continue
        unexpected.append(path.name)
    if unexpected:
        raise SystemExit("invalid bounded-action-loop fixtures passed: " + ", ".join(unexpected))
    print("OK: bounded action loop fixtures validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
