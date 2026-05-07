#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "ops-history" / "agentplane-ops-history-contract.example.json"
ALLOWED_EVENT_CLASSES = {
    "agentplane.validation",
    "agentplane.placement",
    "agentplane.run",
    "agentplane.replay",
    "artifact.reference",
    "policy.decision",
    "redaction.tombstone",
    "agent.handoff",
}


def main() -> int:
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    intake = data.get("intake", {})
    if intake.get("dryRun") is not True:
        raise SystemExit("AgentPlane OpsHistory intake must remain dryRun=true in the example")
    if not str(intake.get("contextPackRef", "")).startswith("urn:srcos:context-pack:"):
        raise SystemExit("contextPackRef must be a SourceOS context-pack URN")
    if not intake.get("policyDecisionRefs"):
        raise SystemExit("intake must include policyDecisionRefs")
    if not intake.get("agentRegistryRefs"):
        raise SystemExit("intake must include agentRegistryRefs")

    events = data.get("emittedEvents", [])
    if not events:
        raise SystemExit("expected emittedEvents")
    for event in events:
        if event.get("eventClass") not in ALLOWED_EVENT_CLASSES:
            raise SystemExit(f"unexpected eventClass: {event.get('eventClass')}")
        if event.get("payloadMode") != "ref-only":
            raise SystemExit("initial AgentPlane OpsHistory events must be ref-only")
        if not event.get("agentPlaneArtifactRefs"):
            raise SystemExit("AgentPlane event missing artifact refs")
        if not event.get("policyDecisionRefs"):
            raise SystemExit("AgentPlane event missing policy decision refs")

    print(json.dumps({"ok": True, "events": len(events)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
