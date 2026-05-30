#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "integration" / "sourceos-interaction-evidence-binding.v0.1.schema.json"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "integration"
VALID = FIXTURE_DIR / "sourceos-interaction-evidence-binding.valid.json"
INVALIDS = [
    FIXTURE_DIR / "sourceos-interaction-evidence-binding.missing-replay.invalid.json",
    FIXTURE_DIR / "sourceos-interaction-evidence-binding.raw-log.invalid.json",
]

REQUIRED_BOUNDARIES = {
    "agentplane": "execution-evidence-replay-authority",
    "sourceos_spec": "canonical-interaction-schema-owner",
    "policy_fabric": "policy-admission-authority",
    "agent_registry": "identity-grant-authority",
    "memory_mesh": "memory-context-pack-authority",
    "noetica": "browser-chat-surface",
    "agent_term": "terminal-operator-surface",
    "superconscious": "task-cognition-coordinator",
}

FORBIDDEN_TERMS = {
    "raw stdout",
    "raw stderr",
    "unrestricted shell output",
    "token=",
    "api key",
    "credential",
    "secret",
    "private chain-of-thought",
    "private reasoning",
    "unrestricted transcript",
}

REQUIRED_CLAIM_PHRASES = (
    "AgentPlane attaches execution",
    "does not own Policy Fabric admission",
    "Agent Registry grants",
    "Memory Mesh context-pack semantics",
    "Noetica UI state",
    "AgentTerm terminal state",
    "SourceOSInteractionEvent schema ownership",
)


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be object")
    return data


def check(record: dict[str, Any]) -> None:
    schema = load(SCHEMA)
    jsonschema.validate(record, schema)

    if record["source_interaction_event_ref"] == record["result_interaction_event_ref"]:
        raise ValueError("source/result interaction event refs must be distinct")

    for field in (
        "validation_artifact_ref",
        "placement_decision_ref",
        "run_artifact_ref",
        "replay_ref",
    ):
        value = str(record[field])
        if "#sha256:" not in value:
            raise ValueError(f"{field} must carry hash-qualified artifact ref")

    if not record["evidence_artifact_refs"]:
        raise ValueError("evidence_artifact_refs required")

    boundaries = record["authority_boundaries"]
    for key, expected in REQUIRED_BOUNDARIES.items():
        if boundaries.get(key) != expected:
            raise ValueError(f"authority boundary drift for {key}: expected {expected!r}")

    if record["payload_mode"] not in {"metadata-only", "summary", "ref-only", "inline-bounded", "redacted"}:
        raise ValueError("invalid payload_mode")

    serialized = json.dumps(record, sort_keys=True).lower()
    for term in FORBIDDEN_TERMS:
        if term in serialized:
            raise ValueError(f"forbidden raw/sensitive payload term present: {term}")

    claim_boundary = record["claim_boundary"]
    for phrase in REQUIRED_CLAIM_PHRASES:
        if phrase not in claim_boundary:
            raise ValueError(f"claim_boundary must include {phrase!r}")


def validate_file(path: Path) -> None:
    check(load(path))


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        validate_file(Path(argv[1]))
        print("OK: SourceOS interaction evidence binding validated")
        return 0

    if len(argv) != 1:
        print("usage: validate_sourceos_interaction_evidence_binding.py [fixture.json]", file=sys.stderr)
        return 2

    validate_file(VALID)
    unexpected: list[str] = []
    for path in INVALIDS:
        try:
            validate_file(path)
        except Exception:
            continue
        unexpected.append(path.name)
    if unexpected:
        raise SystemExit("invalid SourceOS interaction evidence fixtures passed: " + ", ".join(unexpected))
    print("OK: SourceOS interaction evidence binding fixtures validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
