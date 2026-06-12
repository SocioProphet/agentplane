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
SCHEMA = ROOT / "schemas" / "reasoning-run-evidence-receipt.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "reasoning-run"

VALID_REPLAY_CLASSES = {"exact", "best-effort", "evidence-only", "non-replayable-side-effect"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    posture = data.get("safe_trace_posture", {})
    if posture.get("raw_private_reasoning") != "not-collected":
        problems.append("safe_trace_posture.raw_private_reasoning must be not-collected")
    if posture.get("mode") != "operational-trace-only":
        problems.append("safe_trace_posture.mode must be operational-trace-only")

    replay_class = data.get("replay_class")
    if replay_class not in VALID_REPLAY_CLASSES:
        problems.append(f"replay_class invalid: {replay_class}")

    # benchmark_passed=false must not have reasoning_status=completed
    if data.get("benchmark_passed") is False and data.get("reasoning_status") == "completed":
        problems.append("benchmark_passed=false must not have reasoning_status=completed")

    # hellgraph_evidence_refs required non-empty
    if not data.get("hellgraph_evidence_refs"):
        problems.append("hellgraph_evidence_refs must not be empty")

    # non_claims required
    if not data.get("non_claims"):
        problems.append("non_claims must not be empty")

    # run_id must be present
    if not data.get("run_id"):
        problems.append("run_id is required")

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
        raise SystemExit("missing valid reasoning-run fixtures")

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
        raise SystemExit("missing reject reasoning-run fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": reasoning run evidence — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
