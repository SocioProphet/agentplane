#!/usr/bin/env python3
"""Read-only Superconscious ReasoningRun import validator.

This script accepts a Superconscious run directory containing SourceOS canonical
reasoning artifacts and emits an AgentPlane-side import report. It does not seal
or mutate evidence; it validates the handoff shape that AgentPlane can later
promote into its evidence lifecycle.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_CANONICAL = [
    "reasoning-events.sourceos.jsonl",
    "reasoning-run.sourceos.json",
    "reasoning-receipt.json",
    "reasoning-replay-plan.json",
    "reasoning-benchmark.json",
]
VALID_REPLAY_CLASSES = {"exact", "best-effort", "evidence-only", "non-replayable-side-effect"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def validate_superconscious_run(run_dir: Path) -> Dict[str, Any]:
    run_dir = run_dir.resolve()
    errors: List[str] = []

    for name in REQUIRED_CANONICAL:
        if not (run_dir / name).exists():
            errors.append(f"missing canonical artifact: {name}")

    if errors:
        return _report(run_dir, None, errors)

    events = load_jsonl(run_dir / "reasoning-events.sourceos.jsonl")
    reasoning_run = load_json(run_dir / "reasoning-run.sourceos.json")
    receipt = load_json(run_dir / "reasoning-receipt.json")
    replay_plan = load_json(run_dir / "reasoning-replay-plan.json")
    benchmark = load_json(run_dir / "reasoning-benchmark.json")

    run_id = reasoning_run.get("id")
    if reasoning_run.get("type") != "ReasoningRun":
        errors.append("reasoning-run.sourceos.json type must be ReasoningRun")
    if not str(run_id or "").startswith("urn:srcos:reasoning-run:"):
        errors.append("ReasoningRun.id must be a urn:srcos:reasoning-run URN")
    if reasoning_run.get("safeTrace", {}).get("mode") != "operational-trace-only":
        errors.append("ReasoningRun.safeTrace.mode must be operational-trace-only")
    if reasoning_run.get("safeTrace", {}).get("rawPrivateReasoning") != "not-collected":
        errors.append("ReasoningRun.safeTrace.rawPrivateReasoning must be not-collected")

    for index, event in enumerate(events, start=1):
        if event.get("type") != "ReasoningEvent":
            errors.append(f"reasoning-events.sourceos.jsonl line {index} type must be ReasoningEvent")
        if event.get("runRef") != run_id:
            errors.append(f"reasoning-events.sourceos.jsonl line {index} runRef mismatch")
        if event.get("traceLevel") == "denied":
            errors.append(f"reasoning-events.sourceos.jsonl line {index} must not emit denied trace content")

    event_refs = set(reasoning_run.get("eventRefs", []))
    event_ids = {event.get("id") for event in events}
    missing_event_refs = sorted(ref for ref in event_refs if ref not in event_ids)
    if missing_event_refs:
        errors.append(f"ReasoningRun.eventRefs not found in event stream: {missing_event_refs}")

    if receipt.get("type") != "ReasoningReceipt":
        errors.append("reasoning-receipt.json type must be ReasoningReceipt")
    if receipt.get("runRef") != run_id:
        errors.append("ReasoningReceipt.runRef mismatch")
    if not receipt.get("traceHash"):
        errors.append("ReasoningReceipt.traceHash is required")

    if replay_plan.get("type") != "ReasoningReplayPlan":
        errors.append("reasoning-replay-plan.json type must be ReasoningReplayPlan")
    if replay_plan.get("runRef") != run_id:
        errors.append("ReasoningReplayPlan.runRef mismatch")
    if replay_plan.get("replayClass") not in VALID_REPLAY_CLASSES:
        errors.append("ReasoningReplayPlan.replayClass is invalid")

    if benchmark.get("type") != "ReasoningBenchmark":
        errors.append("reasoning-benchmark.json type must be ReasoningBenchmark")
    if benchmark.get("runRef") != run_id:
        errors.append("ReasoningBenchmark.runRef mismatch")
    if benchmark.get("passed") is not True:
        errors.append("ReasoningBenchmark.passed must be true for AgentPlane import readiness")

    return _report(
        run_dir,
        {
            "runId": run_id,
            "status": reasoning_run.get("status"),
            "eventCount": len(events),
            "receiptRef": receipt.get("id"),
            "replayPlanRef": replay_plan.get("id"),
            "replayClass": replay_plan.get("replayClass"),
            "benchmarkRef": benchmark.get("id"),
            "benchmarkSuite": benchmark.get("suite"),
            "benchmarkPassed": benchmark.get("passed"),
            "safeTraceMode": reasoning_run.get("safeTrace", {}).get("mode"),
            "rawPrivateReasoning": reasoning_run.get("safeTrace", {}).get("rawPrivateReasoning"),
        },
        errors,
    )


def _report(run_dir: Path, summary: Dict[str, Any] | None, errors: List[str]) -> Dict[str, Any]:
    return {
        "kind": "AgentPlaneSuperconsciousReasoningImportReport",
        "version": "0.1.0",
        "validatedAt": utc_now(),
        "runDir": str(run_dir),
        "result": "pass" if not errors else "fail",
        "summary": summary or {},
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate/import a Superconscious canonical reasoning run directory.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None, help="Optional path to write the import report JSON")
    args = parser.parse_args()

    try:
        report = validate_superconscious_run(args.run_dir)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[superconscious-import] ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    if report["result"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
