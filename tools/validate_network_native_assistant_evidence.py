#!/usr/bin/env python3
"""Validate Network/BYOM/Native Assistant evidence schema and examples.

This bootstrap validator is intentionally stdlib-only. It catches malformed JSON,
missing schema/example files, and wrong evidence kind declarations without adding
runtime dependencies to AgentPlane validation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_EXAMPLES = [
    (
        "NetworkDoorPlanEvidence",
        ROOT / "schemas" / "network-door-plan-evidence.schema.v0.1.json",
        ROOT / "examples" / "evidence" / "network-door-plan-evidence.example.json",
    ),
    (
        "ExternalModelProviderRouteEvidence",
        ROOT / "schemas" / "external-model-provider-route-evidence.schema.v0.1.json",
        ROOT / "examples" / "evidence" / "external-model-provider-route-evidence.example.json",
    ),
    (
        "NativeAssistantBridgeEvidence",
        ROOT / "schemas" / "native-assistant-bridge-evidence.schema.v0.1.json",
        ROOT / "examples" / "evidence" / "native-assistant-bridge-evidence.example.json",
    ),
]


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"expected JSON object in {path.relative_to(ROOT)}")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_pair(kind: str, schema_path: Path, example_path: Path) -> None:
    schema = load_json(schema_path)
    example = load_json(example_path)

    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{schema_path.relative_to(ROOT)} must use JSON Schema draft 2020-12")
    require(schema.get("type") == "object", f"{schema_path.relative_to(ROOT)} must describe an object")
    require("properties" in schema, f"{schema_path.relative_to(ROOT)} must define properties")
    require("required" in schema, f"{schema_path.relative_to(ROOT)} must define required fields")
    require(schema.get("properties", {}).get("kind", {}).get("const") == kind, f"{schema_path.relative_to(ROOT)} must declare kind const {kind}")
    require(example.get("kind") == kind, f"{example_path.relative_to(ROOT)} kind must be {kind}")
    require(example.get("policyHash"), f"{example_path.relative_to(ROOT)} must include policyHash")

    if kind == "NetworkDoorPlanEvidence":
        require(example.get("destinationStored") is False, "NetworkDoorPlanEvidence example must not store destination text")
        side_effects = example.get("sideEffects", {})
        require(side_effects.get("mutatedFirewall") is False, "NetworkDoorPlanEvidence must not mutate firewall in example")
        require(side_effects.get("installedMesh") is False, "NetworkDoorPlanEvidence must not install mesh in example")
    elif kind == "ExternalModelProviderRouteEvidence":
        require(example.get("authInline") is False, "ExternalModelProviderRouteEvidence must not inline auth")
        require(example.get("promptStored") is False, "ExternalModelProviderRouteEvidence must not store prompts")
        require(example.get("contactsProvider") is False, "ExternalModelProviderRouteEvidence example must not contact provider")
    elif kind == "NativeAssistantBridgeEvidence":
        require(example.get("invokesAssistant") is False, "NativeAssistantBridgeEvidence example must not invoke assistant")
        require(example.get("promptStored") is False, "NativeAssistantBridgeEvidence must not store prompts")
        policy = example.get("policy", {})
        require(policy.get("rawAppDatabaseAccessAllowed") is False, "NativeAssistantBridgeEvidence must deny raw app DB access")


def main() -> int:
    try:
        for kind, schema_path, example_path in SCHEMA_EXAMPLES:
            validate_pair(kind, schema_path, example_path)
            print(f"ok: {kind}")
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: validated Network/BYOM/Native Assistant evidence schemas and examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
