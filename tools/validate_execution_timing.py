#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "suite-execution-timing.example.json"
REQUIRED_META = {"taskId", "agentId", "agentKind", "workstream", "repo"}
REQUIRED_SPEC = {"command", "queueStartedAt", "runStartedAt", "runCompletedAt", "wallClockMs", "status", "exitCode", "retryCount", "stdoutRef", "stderrRef", "artifactRefs", "evidenceRef", "replayRef"}
ALLOWED_AGENT_KINDS = {"codex", "copilot", "human", "local-cli", "system"}
ALLOWED_STATUS = {"queued", "running", "succeeded", "failed", "cancelled", "blocked"}


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not EXAMPLE.exists():
        return fail(f"missing {EXAMPLE}")
    data = json.loads(EXAMPLE.read_text())
    if data.get("apiVersion") != "agentplane.socioprophet.dev/v1":
        return fail("apiVersion must be agentplane.socioprophet.dev/v1")
    if data.get("kind") != "AgentExecutionRecord":
        return fail("kind must be AgentExecutionRecord")
    meta = data.get("metadata", {})
    spec = data.get("spec", {})
    missing_meta = sorted(REQUIRED_META - set(meta))
    if missing_meta:
        return fail(f"missing metadata fields: {missing_meta}")
    missing_spec = sorted(REQUIRED_SPEC - set(spec))
    if missing_spec:
        return fail(f"missing spec fields: {missing_spec}")
    if meta.get("agentKind") not in ALLOWED_AGENT_KINDS:
        return fail("metadata.agentKind is invalid")
    if spec.get("status") not in ALLOWED_STATUS:
        return fail("spec.status is invalid")
    if not isinstance(spec.get("artifactRefs"), list):
        return fail("spec.artifactRefs must be a list")
    if int(spec.get("retryCount")) < 0:
        return fail("spec.retryCount must be non-negative")
    queue_started = parse_ts(spec["queueStartedAt"])
    run_started = parse_ts(spec["runStartedAt"])
    run_completed = parse_ts(spec["runCompletedAt"])
    if not queue_started <= run_started <= run_completed:
        return fail("timestamps must satisfy queueStartedAt <= runStartedAt <= runCompletedAt")
    derived_wall_ms = int((run_completed - run_started).total_seconds() * 1000)
    if int(spec["wallClockMs"]) != derived_wall_ms:
        return fail(f"wallClockMs must equal derived run duration {derived_wall_ms}")
    print("OK: validated agent execution timing example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
