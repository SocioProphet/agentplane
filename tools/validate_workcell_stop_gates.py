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
SCHEMA_OVERRIDE = ROOT / "schemas" / "human-override-artifact.schema.v0.1.json"
SCHEMA_REPLAY = ROOT / "schemas" / "guardrail-replay-artifact.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "workcell-stop-gates"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def schema_for(data: dict[str, Any], schemas: dict[str, Any]) -> dict[str, Any]:
    kind = data.get("kind", "")
    if kind == "HumanOverrideArtifact":
        return schemas["override"]
    if kind == "GuardrailReplayArtifact":
        return schemas["replay"]
    raise ValueError(f"unknown kind: {kind}")


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    kind = data.get("kind")

    if kind == "HumanOverrideArtifact":
        if not data.get("override_reason", "").strip():
            problems.append("override_reason must not be empty")
        if not data.get("authority_ref"):
            problems.append("authority_ref is required; no anonymous overrides")

    if kind == "GuardrailReplayArtifact":
        if data.get("replay_status") == "diverged" and not data.get("divergence_record"):
            problems.append("replay_status=diverged requires divergence_record")

    if not data.get("non_claims"):
        problems.append("non_claims must not be empty")

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
        "override": load_json(SCHEMA_OVERRIDE),
        "replay": load_json(SCHEMA_REPLAY),
    }
    failed = False

    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid workcell-stop-gates fixtures")

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
        raise SystemExit("missing reject workcell-stop-gates fixtures")

    for path in rejects:
        problems = validate_file(path, schemas)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": workcell stop gates — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
