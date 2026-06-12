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
SCHEMA = ROOT / "schemas" / "concept-to-artifact-lineage-receipt.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "concept-lineage"

NON_REPLAYABLE_MODES = {"non_replayable_interpretive_judgment"}
REPLAYABLE_MODES = {"deterministic_extraction", "model_assisted_extraction", "human_review"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    non_claims = data.get("non_claims", [])
    if not non_claims:
        problems.append("non_claims must not be empty")

    extraction_mode = data.get("extraction_mode")
    replay = data.get("replay_semantics", {})

    if extraction_mode in NON_REPLAYABLE_MODES:
        if replay.get("is_replayable") is not False:
            problems.append("non_replayable_interpretive_judgment must have is_replayable=false")
        if not replay.get("non_replayable_reason"):
            problems.append("non_replayable_interpretive_judgment requires non_replayable_reason")

    if extraction_mode in REPLAYABLE_MODES:
        if replay.get("is_replayable") is False and not replay.get("non_replayable_reason"):
            problems.append("non-replayable receipt with replayable extraction_mode requires non_replayable_reason")

    # geometry_projection.distortion_assumptions must be non-empty when present
    geo = data.get("geometry_projection")
    if geo:
        if not geo.get("distortion_assumptions"):
            problems.append("geometry_projection.distortion_assumptions must not be empty")

    # dymaxion_metric.assumptions must be non-empty when present
    metric = data.get("dymaxion_metric")
    if metric:
        if not metric.get("assumptions"):
            problems.append("dymaxion_metric.assumptions must not be empty")

    # No unreviewed model rationale stored as proof:
    # commons_impact with evidence_basis=asserted_without_evidence must not be validated
    commons = data.get("commons_impact")
    if commons:
        if commons.get("evidence_basis") == "asserted_without_evidence" and commons.get("validation_state") in ("peer_reviewed",):
            problems.append("commons_impact with asserted_without_evidence basis cannot be peer_reviewed")

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
        raise SystemExit("missing valid concept-lineage fixtures")

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
        raise SystemExit("missing reject concept-lineage fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": concept-to-artifact lineage — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
