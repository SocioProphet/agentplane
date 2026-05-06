#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
INTAKE_SCHEMA = ROOT / "schemas" / "ops-history-context-intake.schema.json"
EVENT_SCHEMA = ROOT / "schemas" / "ops-history-agentplane-event.schema.json"
INTAKE_EXAMPLE = ROOT / "examples" / "ops-history" / "context-intake.example.json"
EVENTS_EXAMPLE = ROOT / "examples" / "ops-history" / "agentplane-events.example.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    intake_schema = load(INTAKE_SCHEMA)
    event_schema = load(EVENT_SCHEMA)
    jsonschema.validators.validator_for(intake_schema).check_schema(intake_schema)
    jsonschema.validators.validator_for(event_schema).check_schema(event_schema)

    intake = load(INTAKE_EXAMPLE)
    jsonschema.validate(intake, intake_schema)
    if intake.get("dryRun") is not True:
        raise SystemExit("context intake example must remain dryRun=true")

    events_doc = load(EVENTS_EXAMPLE)
    events = events_doc.get("events", [])
    if not events:
        raise SystemExit("agentplane event example must include events")
    for event in events:
        jsonschema.validate(event, event_schema)
        if event.get("payloadMode") != "ref-only":
            raise SystemExit("AgentPlane OpsHistory events should be ref-only in initial examples")

    print(json.dumps({"ok": True, "checked": [str(INTAKE_EXAMPLE), str(EVENTS_EXAMPLE)]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
