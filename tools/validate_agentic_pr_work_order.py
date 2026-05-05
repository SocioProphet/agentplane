#!/usr/bin/env python3
"""Compact stdlib validator for AgenticPRWorkOrder schema/example surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "agentic-pr-work-order.schema.v0.1.json"
EXAMPLE = ROOT / "examples" / "agentic-pr-work-order.example.json"


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing {path.relative_to(ROOT)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"expected object in {path.relative_to(ROOT)}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    schema = load(SCHEMA)
    example = load(EXAMPLE)

    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema draft mismatch")
    require(schema.get("title") == "Agentic PR Work Order", "schema title mismatch")
    require(schema.get("properties", {}).get("kind", {}).get("const") == "AgenticPRWorkOrder", "schema kind const mismatch")

    require(example.get("apiVersion") == "agentplane.socioprophet.org/v0.1", "example apiVersion mismatch")
    require(example.get("kind") == "AgenticPRWorkOrder", "example kind mismatch")

    metadata = example.get("metadata", {})
    spec = example.get("spec", {})
    require(metadata.get("repository") == "SocioProphet/agentplane", "repository mismatch")
    require(str(metadata.get("issueRef", "")).endswith("/issues/82"), "issueRef must point to agentplane#82")

    authority = spec.get("authority", {})
    require(authority.get("separationOfDuties") is True, "separationOfDuties must be true")
    actors = {authority.get("implementationAgent"), authority.get("reviewAgent"), authority.get("mergeGate")}
    require(len(actors) == 3, "implementation/review/merge actors must be distinct")

    scope = spec.get("scope", {})
    expected_files = set(scope.get("expectedFiles", []))
    require("schemas/agentic-pr-work-order.schema.v0.1.json" in expected_files, "schema missing from expectedFiles")
    require("examples/agentic-pr-work-order.example.json" in expected_files, "example missing from expectedFiles")
    require(scope.get("maxChangedFiles", 0) >= len(expected_files), "maxChangedFiles too small")

    validation = spec.get("validation", {})
    commands = set(validation.get("requiredCommands", []))
    require("git status --short" in commands, "missing git status validation command")
    require("git diff --stat" in commands, "missing git diff validation command")
    require(validation.get("evidenceRequired") is True, "evidenceRequired must be true")

    output = spec.get("output", {})
    required_sections = set(output.get("requiredPrSections", []))
    for section in {"summary", "changed-files", "validation", "known-gaps", "self-critique", "linked-issue", "policy-evidence"}:
        require(section in required_sections, f"missing PR section {section}")

    policy_refs = spec.get("policyRefs", {})
    require(policy_refs.get("diffHygieneGate") == "SocioProphet/policy-fabric#44", "diffHygieneGate ref mismatch")

    print("OK: validated AgenticPRWorkOrder schema and example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
