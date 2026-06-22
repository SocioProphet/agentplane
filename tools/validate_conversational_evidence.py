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
SCHEMA_CAE = ROOT / "schemas" / "conversational-action-evidence.schema.v0.1.json"
SCHEMA_CRR = ROOT / "schemas" / "conversational-replay-record.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "conversational-evidence"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def schema_for(data: dict[str, Any], schemas: dict[str, Any]) -> dict[str, Any]:
    kind = data.get("kind", "")
    if kind == "ConversationalActionEvidence":
        return schemas["cae"]
    if kind == "ConversationalReplayRecord":
        return schemas["crr"]
    raise ValueError(f"unknown kind: {kind}")


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    kind = data.get("kind")

    if kind == "ConversationalActionEvidence":
        hg_refs = data.get("hellgraph_evidence_refs", [])
        if not hg_refs:
            problems.append("hellgraph_evidence_refs must not be empty")

        replay = data.get("replay_linkage", {})
        if replay.get("replay_divergence_detected") and not replay.get("replay_divergence_ref"):
            problems.append("replay_divergence_detected=true requires replay_divergence_ref")

        action_type = data.get("action_type")
        policy_outcome = data.get("policy_outcome")
        if action_type == "approval_denial" and policy_outcome not in ("deny", "escalate"):
            problems.append("approval_denial action_type requires deny or escalate policy_outcome")

    if kind == "ConversationalReplayRecord":
        non_claims = data.get("non_claims", [])
        if not non_claims:
            problems.append("non_claims must not be empty")

        if data.get("replay_status") == "diverged" and not data.get("divergence_record"):
            problems.append("replay_status=diverged requires divergence_record")

        div_rec = data.get("divergence_record")
        if div_rec and data.get("replay_status") != "diverged":
            problems.append("divergence_record present but replay_status is not diverged")

    return problems


def validate_file(path: Path, schemas: dict[str, Any]) -> list[str]:
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"parse error: {exc}"]
    try:
        schema = schema_for(data, schemas)
        jsonschema.validate(data, schema)
    except (jsonschema.ValidationError, ValueError) as exc:
        return [f"schema: {exc}"]
    return check_policy_gates(data)


def main() -> int:
    schemas = {
        "cae": load_json(SCHEMA_CAE),
        "crr": load_json(SCHEMA_CRR),
    }
    failed = False

    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid conversational-evidence fixtures")

    for path in valids:
        problems = validate_file(path, schemas)
        if problems:
            print(f"FAIL (valid): {path.name}")
            for p in problems:
                print(f"  - {p}")
            failed = True
        else:
            print(f"ok: {path.name}")

    rejects = sorted(FIXTURES.glob("reject.*.json"))
    if not rejects:
        raise SystemExit("missing reject conversational-evidence fixtures")

    for path in rejects:
        problems = validate_file(path, schemas)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": conversational evidence — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
