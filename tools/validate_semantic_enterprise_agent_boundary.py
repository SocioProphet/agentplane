#!/usr/bin/env python3
"""Validate AgentPlane's Semantic Enterprise v0.1 context/admission fixture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/semantic-enterprise/v0.1/agent-context-boundary.example.json"

REQUIRED_SECTORS = {"finance", "threat-intel", "investigation", "supply-chain", "defense-c2"}
REQUIRED_ADMISSION_FLAGS = {
    "requires_declared_sector_context",
    "requires_source_provenance",
    "requires_named_graph_reference",
    "treats_examples_as_evidence_not_instructions",
    "preserves_runtime_observation_boundary",
}
REQUIRED_CLOSURE_KEYS = {
    "inside_source",
    "outside_agent_runtime",
    "boundary_membrane",
    "feedback_surface",
}
REQUIRED_DISALLOWED_CLAIMS = {
    "live_ingestion_completed",
    "production_graph_mutated",
    "operational_playbook_executed",
}


def main() -> int:
    errors: list[str] = []
    if not FIXTURE.is_file():
        print(f"missing fixture: {FIXTURE}")
        return 1

    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}")
        return 1

    if data.get("contract") != "agentplane.semantic-enterprise.context-boundary":
        errors.append("unexpected contract identifier")
    if data.get("version") != "0.1.0":
        errors.append("unexpected contract version")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        expected = {
            "repository": "SocioProphet/ontogenesis",
            "release": "semantic-enterprise-v0.1.0",
            "manifest_path": "manifests/semantic_enterprise_v0_1_manifest.json",
            "rollup_registry_path": "catalog/semantic_enterprise_v0_1_registry.ttl",
            "named_graph_fixture_path": "examples/named-graphs/semantic_sector_named_graphs.ttl",
        }
        for key, value in expected.items():
            if source.get(key) != value:
                errors.append(f"source.{key} expected {value!r}, got {source.get(key)!r}")

    admission = data.get("admission_policy")
    if not isinstance(admission, dict):
        errors.append("admission_policy must be an object")
    else:
        missing = REQUIRED_ADMISSION_FLAGS.difference(admission)
        if missing:
            errors.append(f"admission_policy missing keys: {sorted(missing)}")
        for key in REQUIRED_ADMISSION_FLAGS.intersection(admission):
            if admission.get(key) is not True:
                errors.append(f"admission_policy.{key} must be true")

    contexts = data.get("allowed_sector_contexts")
    if not isinstance(contexts, list):
        errors.append("allowed_sector_contexts must be a list")
    else:
        sectors = {context.get("sector") for context in contexts if isinstance(context, dict)}
        if sectors != REQUIRED_SECTORS:
            errors.append(f"expected sectors {sorted(REQUIRED_SECTORS)}, got {sorted(sectors)}")
        for context in contexts:
            if not isinstance(context, dict):
                errors.append("sector context must be an object")
                continue
            sector = context.get("sector")
            if not str(context.get("scenario_path", "")).startswith("examples/scenarios/"):
                errors.append(f"{sector} scenario_path must point to examples/scenarios")
            if not str(context.get("query_path", "")).startswith("examples/queries/"):
                errors.append(f"{sector} query_path must point to examples/queries")
            if not str(context.get("named_graph_uri_fragment", "")).startswith("graphs/scenarios/"):
                errors.append(f"{sector} named graph URI fragment must point to graphs/scenarios")
            surface = str(context.get("agent_context_surface", ""))
            if not surface.startswith("semantic-enterprise.") or not surface.endswith(".context.v0.1"):
                errors.append(f"{sector} agent_context_surface has unexpected format")

    task = data.get("task_context_example")
    if not isinstance(task, dict):
        errors.append("task_context_example must be an object")
    else:
        declared_sector = task.get("declared_sector_context")
        if declared_sector not in REQUIRED_SECTORS:
            errors.append("task_context_example declared_sector_context must be a known sector")
        evidence_refs = task.get("evidence_refs")
        if not isinstance(evidence_refs, list) or len(evidence_refs) < 3:
            errors.append("task_context_example must include scenario, query, and graph evidence refs")
        disallowed = set(task.get("disallowed_runtime_claims") or [])
        if not REQUIRED_DISALLOWED_CLAIMS.issubset(disallowed):
            errors.append(f"task_context_example missing disallowed runtime claims: {sorted(REQUIRED_DISALLOWED_CLAIMS.difference(disallowed))}")

    closure = data.get("closure_model")
    if not isinstance(closure, dict):
        errors.append("closure_model must be an object")
    else:
        missing = REQUIRED_CLOSURE_KEYS.difference(closure)
        if missing:
            errors.append(f"closure_model missing keys: {sorted(missing)}")
        for key in REQUIRED_CLOSURE_KEYS.intersection(closure):
            if not isinstance(closure.get(key), str) or not closure[key].strip():
                errors.append(f"closure_model.{key} must be a non-empty string")

    if errors:
        print("Semantic Enterprise agent-boundary validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Semantic Enterprise agent-boundary validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
