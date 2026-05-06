#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "sourceos-context-tool-provider-evidence.schema.v0.1.json"
EXAMPLE = ROOT / "examples" / "sourceos" / "sourceos-context-tool-provider-evidence.example.json"

REQUIRED_DENIED = {
    "repo.write",
    "hooks.install",
    "hooks.modify",
    "dashboard.expose",
    "pty.spawn",
    "memory.persist.native",
    "network.callback",
    "external.update_check",
    "external.feedback_submit",
    "desktop.search.bypass_lampstand",
    "home.scan.unbounded",
    "system.scan",
    "symlink.follow",
}


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
        print("SourceOS context tool provider evidence failed validation:")
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            print(f" - {location}: {error.message}")
        return 1

    denied = set(example["deniedCapabilities"])
    missing = sorted(REQUIRED_DENIED - denied)
    if missing:
        print(f"SourceOS context provider evidence is missing denied capabilities: {missing}")
        return 1

    flags = example["sideEffectFlags"]
    for flag in ("repoWrites", "hookMutation", "dashboardExposure", "ptySpawn", "externalCallbacks", "nativeMemoryPersistence"):
        if flags[flag] is not False:
            print(f"sideEffectFlags.{flag} must remain false")
            return 1
    if flags["lampstandPublishRequiresExplicitFlag"] is not True:
        print("Lampstand publish must require an explicit flag")
        return 1

    if example["policyProfile"] != "sourceos.repo_context.read_only":
        print("Policy profile drifted from sourceos.repo_context.read_only")
        return 1

    if "lampstand.search_record.publish.local" not in example["allowedCapabilities"]:
        print("Expected governed Lampstand local publish capability")
        return 1

    print("SourceOS context tool provider evidence validates against schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
