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
SCHEMA = ROOT / "schemas" / "shir-governed-chain-job.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "shir-chain"

REVIEW_STATUSES = {"requires_review", "failed_closed"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    status = data.get("job_status")
    failure_mode = data.get("failure_mode")
    policy_outcome = data.get("policy_outcome")

    # requires_review and failed_closed must declare failure_mode and policy_outcome
    if status in REVIEW_STATUSES:
        if not failure_mode:
            problems.append(f"job_status={status} requires failure_mode")
        if not policy_outcome:
            problems.append(f"job_status={status} requires policy_outcome")

    # fail_closed policy_mode + semantic_leakage_blocking → failed_closed status
    policy_mode = data.get("policy_mode")
    if policy_mode == "fail_closed" and failure_mode == "semantic_leakage_blocking":
        if status != "failed_closed":
            problems.append("fail_closed policy_mode + semantic_leakage_blocking must set job_status=failed_closed")

    # completed job: chain_receipt stage must be completed
    if status == "completed":
        chain = data.get("stages", {}).get("chain_receipt", {})
        if chain.get("stage_status") != "completed":
            problems.append("completed job requires chain_receipt stage_status=completed")

    # shir-to-pyg must emit projection_loss_report
    artifacts = data.get("artifacts", {})
    stages = data.get("stages", {})
    shir_to_pyg = stages.get("shir_to_pyg", {})
    if shir_to_pyg.get("stage_status") == "completed":
        if not artifacts.get("projection_loss_report_ref"):
            # also check stage artifact_refs
            stage_refs = shir_to_pyg.get("artifact_refs", [])
            if not any("projection-loss" in r for r in stage_refs):
                problems.append("shir_to_pyg completed stage requires projection_loss_report_ref in artifacts or stage artifact_refs")

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
        raise SystemExit("missing valid shir-chain fixtures")

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
        raise SystemExit("missing reject shir-chain fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": SHIR governed chain job — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
