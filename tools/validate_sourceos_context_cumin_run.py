#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "sourceos-context-cumin-run.schema.v0.1.json"
EXAMPLE = ROOT / "examples" / "sourceos" / "sourceos-context-cumin-run.example.json"

MUTATING_FLAGS = (
    "repoWrites",
    "hookMutation",
    "dashboardExposure",
    "ptySpawn",
    "externalCallbacks",
    "nativeMemoryPersistence",
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schema = load_json(SCHEMA)
    example = load_json(EXAMPLE)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.path))
    if errors:
        print("SourceOS context Cumin run failed validation:")
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            print(f" - {location}: {error.message}")
        return 1

    runner = example["runner"]
    if runner["runnerType"] != "cumin":
        print("runner.runnerType must remain cumin")
        return 1
    if runner["forbidLocalMac"] is not True:
        print("runner.forbidLocalMac must remain true")
        return 1
    if runner["executionMode"] != "dry_run":
        print("example executionMode must remain dry_run until real remote runner is approved")
        return 1

    if example["policyProfileRef"] != "policy-fabric://sourceos.repo_context.read_only":
        print("policyProfileRef must bind to Policy Fabric sourceos.repo_context.read_only")
        return 1

    side_effects = example["sideEffectPolicy"]
    for flag in MUTATING_FLAGS:
        if side_effects[flag] is not False:
            print(f"sideEffectPolicy.{flag} must remain false")
            return 1
    if side_effects["lampstandPublishRequiresExplicitFlag"] is not True:
        print("Lampstand publish must require explicit flag")
        return 1

    operation = example["command"]["operation"]
    if operation == "lampstand-publish" and example["command"].get("requiresExplicitPublishFlag") is not True:
        print("lampstand-publish operation must require explicit publish flag")
        return 1

    args = example["command"].get("args", [])
    if "--publish" in args:
        print("dry-run example must not include --publish")
        return 1
    if any("mac" in str(arg).lower() for arg in args):
        print("command args must not reference Mac-local execution")
        return 1

    for root in example["scope"]["rootRefs"]:
        if not str(root).startswith("~/dev/"):
            print(f"rootRef must stay under ~/dev/**: {root}")
            return 1

    print("SourceOS context Cumin run validates against schema and invariants.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
