#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "orggov-work-order-evidence-bridge.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "orggov-bridge"

SHA256_RE = re.compile(r"^sha256:[A-Fa-f0-9]{64}$")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    # output_hash format if present
    output_hash = data.get("output_hash")
    if output_hash and not SHA256_RE.match(output_hash):
        problems.append("output_hash must match sha256:[A-Fa-f0-9]{64}")

    # non_claims required
    if not data.get("non_claims"):
        problems.append("non_claims must not be empty")

    # lifecycle consistency: completed run should have run_artifact_ref
    lifecycle = data.get("lifecycle", {})
    run = lifecycle.get("run", {})
    if run.get("status") == "completed" and not run.get("run_artifact_ref"):
        problems.append("lifecycle.run.status=completed requires run_artifact_ref")

    # replay verified=true requires replay_artifact_ref
    replay = lifecycle.get("replay", {})
    if replay.get("replay_verified") is True and not replay.get("replay_artifact_ref"):
        problems.append("lifecycle.replay.replay_verified=true requires replay_artifact_ref")

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
        raise SystemExit("missing valid orggov-bridge fixtures")

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
        raise SystemExit("missing reject orggov-bridge fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": OrgGov work order evidence bridge — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
