#!/usr/bin/env python3
"""Validate event-capability admission before AgentPlane execution."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

HIGH_RISK_EFFECTS = {"high_risk_actuation", "irreversible_action"}
EXECUTABLE_OUTCOMES = {"allowed", "redacted"}
WAITING_OUTCOMES = {"requires_approval"}
BLOCKING_OUTCOMES = {"denied", "degraded", "requires_local_only"}


def fail(message: str) -> None:
    print(f"ERR: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> Any:
    if not path.exists():
        fail(f"missing event-capability input: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")


def bundle_to_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    capabilities = {item.get("capability_id"): item for item in bundle.get("capabilities", []) if isinstance(item, dict)}
    events = {item.get("event_id"): item for item in bundle.get("events", []) if isinstance(item, dict)}
    records = []
    for reaction in bundle.get("reaction_plans", []):
        if not isinstance(reaction, dict):
            continue
        records.append(
            {
                "record_id": "record:" + str(reaction.get("reaction_id", "unknown")).split(":", 1)[-1],
                "mode": "event-capability-evidence-v0",
                "event": events.get(reaction.get("event_id"), {}),
                "capability": capabilities.get(reaction.get("capability_id"), {}),
                "reaction": reaction,
                "evidence_refs": reaction.get("receipt_refs", []),
            }
        )
    return records


def extract_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        if {"events", "capabilities", "reaction_plans"}.issubset(value):
            return bundle_to_records(value)
        for key in ("records", "results"):
            items = value.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        data = value.get("data")
        if isinstance(data, dict):
            return extract_records(data)
    fail("input must be records/results or a full event-capability bundle")


def admission_for_record(record: dict[str, Any]) -> dict[str, Any]:
    event = record.get("event") if isinstance(record.get("event"), dict) else {}
    capability = record.get("capability") if isinstance(record.get("capability"), dict) else {}
    reaction = record.get("reaction") if isinstance(record.get("reaction"), dict) else {}
    causality = event.get("causality") if isinstance(event.get("causality"), dict) else {}

    errors: list[str] = []
    warnings: list[str] = []

    event_id = str(event.get("event_id", ""))
    capability_id = str(capability.get("capability_id", ""))
    effect_class = str(capability.get("effect_class", ""))
    policy_outcome = str(reaction.get("policy_outcome", ""))
    idempotency_key = str(causality.get("idempotency_key", ""))
    receipt_refs = record.get("evidence_refs") or reaction.get("receipt_refs") or []

    if not event_id:
        errors.append("missing event_id")
    if not capability_id:
        errors.append("missing capability_id")
    if not idempotency_key:
        errors.append("missing idempotency key")
    if not receipt_refs:
        errors.append("missing evidence receipt references")
    if reaction.get("dead_letter_on_failure") is not True:
        errors.append("dead_letter_on_failure must be true")
    if policy_outcome != capability.get("required_policy_outcome"):
        errors.append("policy outcome does not match capability required_policy_outcome")

    if effect_class in HIGH_RISK_EFFECTS:
        approval_mode = str(capability.get("approval_mode", ""))
        if policy_outcome == "allowed":
            errors.append("high-risk capability cannot be directly allowed in bootstrap event admission")
        if policy_outcome == "requires_approval" and approval_mode not in {"explicit_user_approval", "two_party_approval", "admin_approval"}:
            errors.append("high-risk approval outcome lacks strict approval mode")
        if policy_outcome == "denied":
            warnings.append("high-risk capability was denied; preserve denial receipt for replay")

    if policy_outcome in EXECUTABLE_OUTCOMES and not errors:
        admission = "admitted"
    elif policy_outcome in WAITING_OUTCOMES and not errors:
        admission = "waiting_for_approval"
    elif policy_outcome in BLOCKING_OUTCOMES and not errors:
        admission = "blocked"
    else:
        admission = "invalid"

    return {
        "record_id": record.get("record_id"),
        "event_id": event_id,
        "capability_id": capability_id,
        "effect_class": effect_class,
        "policy_outcome": policy_outcome,
        "idempotency_key": idempotency_key,
        "receipt_refs": receipt_refs,
        "admission": admission,
        "errors": errors,
        "warnings": warnings,
    }


def build_artifact(records: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = [admission_for_record(record) for record in records]
    invalid = [item for item in decisions if item["admission"] == "invalid"]
    return {
        "schema": "agentplane.event_capability_admission.v0.1",
        "artifactId": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {
            "total": len(decisions),
            "admitted": sum(1 for item in decisions if item["admission"] == "admitted"),
            "waiting_for_approval": sum(1 for item in decisions if item["admission"] == "waiting_for_approval"),
            "blocked": sum(1 for item in decisions if item["admission"] == "blocked"),
            "invalid": len(invalid),
        },
        "agentMayExecute": len(invalid) == 0,
        "decisions": decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate event-capability admission before AgentPlane execution.")
    parser.add_argument("--input", required=True, help="Path to event-capability bundle or record list")
    parser.add_argument("--out", help="Optional output path for admission artifact")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if any record is not admitted")
    args = parser.parse_args()

    artifact = build_artifact(extract_records(load_json(Path(args.input))))
    text = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text, end="")

    if artifact["summary"]["invalid"]:
        return 1
    if args.strict and artifact["summary"]["admitted"] != artifact["summary"]["total"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
