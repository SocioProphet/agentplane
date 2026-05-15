#!/usr/bin/env python3
"""Emit an AgentOperationContract artifact through the Workspace Operation Plane.

Every agent-initiated workspace mutation must produce an AgentOperationContract
instead of writing artifacts as hidden side effects. This script is the canonical
emission path for all supported agent operation types.

Supported operation types
--------------------------
  agent.patch.propose       Agent proposes a code patch for review/admission.
  agent.report.create       Agent creates a report artifact.
  agent.metadata.fill       Agent fills metadata fields.
  agent.failure.explain     Agent explains an observed failure.
  agent.remediation.propose Agent proposes a remediation action.
  agent.terminal.assist     Agent assists with a terminal operation.

Output
------
Writes ``agent-operation-contract.json`` to ``bundle.spec.artifacts.outDir``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

OPERATION_TYPES = {
    "agent.patch.propose",
    "agent.report.create",
    "agent.metadata.fill",
    "agent.failure.explain",
    "agent.remediation.propose",
    "agent.terminal.assist",
}

ARTIFACT_TYPES = {
    "patch",
    "report",
    "document",
    "test-result",
    "terminal-transcript",
    "metadata-fill",
}

LIFECYCLE_STATUSES = {
    "created",
    "in-progress",
    "completed",
    "failed",
    "cancelled",
    "compensating",
}

POLICY_RESULTS = {"allow", "deny", "pending", "needs_human"}
AUDIT_LEVELS = {"full", "summary", "minimal"}


def die(msg: str, code: int = 2) -> None:
    print(f"[agent-operation-contract] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"invalid bundle json: {exc}", 2)


def _make_idempotency_key(operation_id: str, retry_count: int) -> str:
    return f"{operation_id}/attempt-{retry_count + 1}"


def build_contract(
    *,
    operation_id: str,
    operation_type: str,
    bundle_ref: str | None,
    acting_for: str,
    scopes: list[str],
    audit_level: str,
    policy_profile_ref: str | None,
    max_tokens: int | None,
    max_wall_seconds: int | None,
    max_files_mutated: int | None,
    status: str,
    retryable: bool,
    retry_count: int,
    artifact_type: str | None,
    artifact_ref: str | None,
    policy_ref: str | None,
    policy_result: str,
    policy_reason: str | None,
    decision: str | None,
    rationale: str | None,
    governance_context: dict[str, Any] | None,
    captured_at: str,
) -> dict[str, Any]:
    completed_at: str | None = None
    started_at: str | None = None
    if status in {"completed", "failed", "cancelled"}:
        started_at = captured_at
        completed_at = captured_at
    elif status == "in-progress":
        started_at = captured_at

    artifacts: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = [
        {
            "eventId": "evt-001",
            "eventType": "created",
            "emittedAt": captured_at,
            "data": {"operationType": operation_type},
        }
    ]

    if status in {"in-progress", "completed", "failed"}:
        events.append({
            "eventId": "evt-002",
            "eventType": "updated",
            "emittedAt": captured_at,
            "data": {"statusTransition": f"created -> {status}"},
        })

    if artifact_type and artifact_ref:
        artifact_id = "artifact-001"
        artifacts.append({
            "artifactId": artifact_id,
            "artifactType": artifact_type,
            "admissionStatus": "pending-review",
            "ref": artifact_ref,
            "createdAt": captured_at,
            "admittedAt": None,
            "admittedBy": None,
        })
        events.append({
            "eventId": f"evt-{len(events) + 1:03d}",
            "eventType": "artifact_emitted",
            "emittedAt": captured_at,
            "data": {
                "artifactId": artifact_id,
                "artifactType": artifact_type,
                "admissionStatus": "pending-review",
            },
        })

    if policy_result:
        events.append({
            "eventId": f"evt-{len(events) + 1:03d}",
            "eventType": "gate_evaluated",
            "emittedAt": captured_at,
            "data": {"result": policy_result, "policyRef": policy_ref},
        })

    if status in {"completed", "failed", "cancelled"}:
        events.append({
            "eventId": f"evt-{len(events) + 1:03d}",
            "eventType": status,
            "emittedAt": captured_at,
            "data": None,
        })

    budget: dict[str, Any] | None = None
    if any(v is not None for v in (max_tokens, max_wall_seconds, max_files_mutated)):
        budget = {
            "maxTokens": max_tokens,
            "maxWallSeconds": max_wall_seconds,
            "maxFilesMutated": max_files_mutated,
        }

    decision_card: dict[str, Any] | None = None
    if decision or rationale:
        decision_card = {
            "decision": decision or "",
            "rationale": rationale or "",
            "constraints": [],
            "reviewRequired": True,
            "reviewedBy": None,
            "reviewedAt": None,
        }

    return {
        "kind": "AgentOperationContract",
        "operationId": operation_id,
        "operationType": operation_type,
        "bundle": bundle_ref,
        "capturedAt": captured_at,
        "authority": {
            "actingFor": acting_for,
            "scope": scopes,
            "budget": budget,
            "policyProfileRef": policy_profile_ref,
            "auditLevel": audit_level,
        },
        "lifecycle": {
            "status": status,
            "startedAt": started_at,
            "completedAt": completed_at,
            "idempotencyKey": _make_idempotency_key(operation_id, retry_count),
            "retryable": retryable,
            "retryCount": retry_count,
            "cancellation": None,
            "compensation": None,
        },
        "tasks": [],
        "events": events,
        "artifacts": artifacts,
        "decisionCard": decision_card,
        "policyGate": {
            "evaluated": True,
            "result": policy_result,
            "policyRef": policy_ref,
            "evaluatedAt": captured_at,
            "reason": policy_reason,
        },
        "replayRef": None,
        "ledgerRef": None,
        "governanceContext": governance_context,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="emit_agent_operation_contract",
        description="Emit an AgentOperationContract through the Workspace Operation Plane.",
    )
    ap.add_argument("bundle", help="Path to bundle.json")
    ap.add_argument("--operation-type", required=True, choices=sorted(OPERATION_TYPES))
    ap.add_argument("--operation-id", required=True)
    ap.add_argument("--acting-for", required=True)
    ap.add_argument("--scope", action="append", dest="scopes", default=[], metavar="SCOPE")
    ap.add_argument("--audit-level", choices=sorted(AUDIT_LEVELS), default="full")
    ap.add_argument("--policy-profile-ref", default=None)
    ap.add_argument("--max-tokens", type=int, default=None)
    ap.add_argument("--max-wall-seconds", type=int, default=None)
    ap.add_argument("--max-files-mutated", type=int, default=None)
    ap.add_argument("--status", choices=sorted(LIFECYCLE_STATUSES), default="completed")
    ap.add_argument("--retryable", action="store_true", default=False)
    ap.add_argument("--retry-count", type=int, default=0)
    ap.add_argument("--artifact-type", choices=sorted(ARTIFACT_TYPES), default=None)
    ap.add_argument("--artifact-ref", default=None)
    ap.add_argument("--policy-ref", default=None)
    ap.add_argument("--policy-result", choices=sorted(POLICY_RESULTS), default="allow")
    ap.add_argument("--policy-reason", default=None)
    ap.add_argument("--decision", default=None)
    ap.add_argument("--rationale", default=None)
    args = ap.parse_args()

    if args.artifact_type and not args.artifact_ref:
        die("--artifact-ref is required when --artifact-type is set", 2)
    if args.artifact_ref and not args.artifact_type:
        die("--artifact-type is required when --artifact-ref is set", 2)
    if not args.scopes:
        die("at least one --scope must be provided", 2)

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        die(f"bundle not found: {bundle_path}", 2)

    bundle = load_bundle(bundle_path)
    metadata = bundle.get("metadata") or {}
    spec = bundle.get("spec") or {}
    name = metadata.get("name")
    version = metadata.get("version")
    if not name or not version:
        die("bundle metadata.name and metadata.version are required", 2)

    out_dir = (spec.get("artifacts") or {}).get("outDir")
    if not out_dir:
        die("bundle spec.artifacts.outDir is required", 2)

    governance_context = spec.get("governanceContext") if isinstance(spec.get("governanceContext"), dict) else None
    captured_at = now_iso()
    contract = build_contract(
        operation_id=args.operation_id,
        operation_type=args.operation_type,
        bundle_ref=f"{name}@{version}",
        acting_for=args.acting_for,
        scopes=args.scopes,
        audit_level=args.audit_level,
        policy_profile_ref=args.policy_profile_ref,
        max_tokens=args.max_tokens,
        max_wall_seconds=args.max_wall_seconds,
        max_files_mutated=args.max_files_mutated,
        status=args.status,
        retryable=args.retryable,
        retry_count=args.retry_count,
        artifact_type=args.artifact_type,
        artifact_ref=args.artifact_ref,
        policy_ref=args.policy_ref,
        policy_result=args.policy_result,
        policy_reason=args.policy_reason,
        decision=args.decision,
        rationale=args.rationale,
        governance_context=governance_context,
        captured_at=captured_at,
    )

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "agent-operation-contract.json"
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[agent-operation-contract] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
