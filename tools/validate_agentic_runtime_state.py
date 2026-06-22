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
SCHEMA = ROOT / "schemas" / "agentic-runtime-state.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "agentic-runtime"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    join_record = data.get("join_record", {})
    if join_record:
        strategy = join_record.get("join_strategy")
        if strategy == "quorum" and "quorum_threshold" not in join_record:
            problems.append("join_strategy=quorum requires quorum_threshold")
        if strategy == "best_of_n" and "best_of_n" not in join_record:
            problems.append("join_strategy=best_of_n requires best_of_n field")
        outcome = join_record.get("join_outcome")
        if outcome == "overridden_human" and not join_record.get("human_selection_ref"):
            problems.append("join_outcome=overridden_human requires human_selection_ref")
        if outcome == "overridden_risk_approved" and not join_record.get("risk_approval_ref"):
            problems.append("join_outcome=overridden_risk_approved requires risk_approval_ref")

    fanout_record = data.get("fanout_record", {})
    if fanout_record:
        if fanout_record.get("fanout_strategy") == "parallel_bounded" and "concurrency_limit" not in fanout_record:
            problems.append("fanout_strategy=parallel_bounded requires concurrency_limit")

    control_signal = data.get("control_signal", {})
    if control_signal:
        if control_signal.get("signal_type") == "requeue_after_delay" and "requeue_delay_seconds" not in control_signal:
            problems.append("signal_type=requeue_after_delay requires requeue_delay_seconds")

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
        raise SystemExit("missing valid agentic-runtime fixtures")

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
        raise SystemExit("missing reject agentic-runtime fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(
        ("PASS" if not failed else "FAIL")
        + f": agentic runtime state — {len(valids)} valid, {len(rejects)} reject"
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
