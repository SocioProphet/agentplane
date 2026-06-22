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
SCHEMA = ROOT / "schemas" / "graph-aware-work-order.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "graph-aware"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []

    ctx = data.get("repo_graph_context", {})
    staleness = ctx.get("graph_artifact_staleness")
    scope_warnings = data.get("scope_warnings", [])

    # stale or missing graph artifact must have a scope_warning
    if staleness in ("stale", "missing"):
        warning_types = {w.get("warning_type") for w in scope_warnings}
        if not (warning_types & {"stale_graph_artifact", "missing_graph_artifact"}):
            problems.append(f"graph_artifact_staleness={staleness} requires a corresponding scope_warning")

    # architectural_impact_claim_requires_graph_evidence=true but graph is missing/stale → must have warning
    cite = data.get("output_citation_requirements", {})
    if cite.get("architectural_impact_claim_requires_graph_evidence") and staleness in ("missing", "unknown"):
        if not scope_warnings:
            problems.append("architectural_impact_claim_requires_graph_evidence=true with missing/unknown graph requires scope_warnings")

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
        raise SystemExit("missing valid graph-aware fixtures")

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
        raise SystemExit("missing reject graph-aware fixtures")

    for path in rejects:
        problems = validate_file(path, schema)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(("PASS" if not failed else "FAIL") + f": graph-aware work orders — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
