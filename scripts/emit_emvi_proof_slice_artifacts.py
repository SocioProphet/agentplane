#!/usr/bin/env python3
"""Bridge a Sociosphere EMVI proof-slice demo artifact into agentplane evidence artifacts.

This is an evidence-shaping bridge, not a real executor. It converts the merged
`sociosphere` proof-slice demo artifact into `RunArtifact`, `ReplayArtifact`, and
`SessionArtifact` files plus a small bridge manifest so downstream agentplane work
has concrete artifacts to consume.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


def die(msg: str, code: int = 2) -> None:
    print(f"[emvi-bridge] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"invalid JSON at {path}: {exc}")
    if not isinstance(data, dict):
        die(f"expected JSON object at {path}")
    return data


def safe_session_suffix(raw: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-")
    return slug or "emvi-proof-slice"


def derive_status(events: list[dict[str, Any]], policy_status: str | None) -> tuple[str, int]:
    bad_statuses = {"failed", "denied"}
    event_statuses = {str(e.get("status", "")).lower() for e in events}
    if policy_status and str(policy_status).lower() in bad_statuses:
        return "failure", 1
    if event_statuses & bad_statuses:
        return "failure", 1
    return "success", 0


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_emvi_proof_slice_artifacts")
    ap.add_argument("demo_artifact", help="Path to sociosphere EMVI demo-artifact.json")
    ap.add_argument("--out-dir", required=True, help="Directory to write agentplane artifacts into")
    ap.add_argument("--bundle-name", default="emvi-proof-slice")
    ap.add_argument("--bundle-version", default="0.1.0")
    ap.add_argument("--lane", default="staging", choices=["staging", "prod"])
    ap.add_argument("--executor", default="sociosphere-proof-slice-smoke")
    ap.add_argument(
        "--backend-intent",
        default="lima-process",
        choices=["qemu", "microvm", "lima-process", "fleet"],
    )
    args = ap.parse_args()

    demo_path = Path(args.demo_artifact)
    if not demo_path.exists():
        die(f"demo artifact not found: {demo_path}")

    artifact = load_json(demo_path)
    if artifact.get("kind") != "EMVIProofSliceDemoArtifact":
        die("input artifact kind must be EMVIProofSliceDemoArtifact")

    action_spec = artifact.get("actionSpec")
    events = artifact.get("events")
    summary = artifact.get("summary") or {}
    if not isinstance(action_spec, dict):
        die("demo artifact missing actionSpec object")
    if not isinstance(events, list):
        die("demo artifact missing events array")

    correlation_ids = summary.get("correlationIds") if isinstance(summary, dict) else None
    if isinstance(correlation_ids, list) and correlation_ids:
        correlation_id = str(correlation_ids[0])
    else:
        correlation_id = "corr-emvi-proof-slice"

    session_suffix = safe_session_suffix(correlation_id)
    session_ref = f"urn:srcos:session:{session_suffix}"
    receipt_ref = f"urn:srcos:receipt:session:{session_suffix}"
    captured_at = now_iso()
    bundle = f"{args.bundle_name}@{args.bundle_version}"
    status, exit_code = derive_status(events, action_spec.get("policy_status"))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_artifact = {
        "kind": "RunArtifact",
        "bundle": bundle,
        "bundlePath": artifact.get("protocolRef"),
        "capturedAt": captured_at,
        "lane": args.lane,
        "executor": args.executor,
        "backendIntent": args.backend_intent,
        "status": status,
        "exitCode": exit_code,
        "stdoutRef": None,
        "stderrRef": None,
        "upstreamArtifacts": {
            "workspaceInventoryRef": None,
            "lockVerificationRef": None,
            "protocolCompatibilityRef": str(demo_path.resolve()),
            "taskRunRefs": [],
        },
    }

    replay_artifact = {
        "kind": "ReplayArtifact",
        "bundle": bundle,
        "capturedAt": captured_at,
        "executor": args.executor,
        "backendIntent": args.backend_intent,
        "inputs": {
            "bundlePath": artifact.get("protocolRef") or str(demo_path.resolve()),
            "bundleRev": None,
            "artifactDir": str(out_dir.resolve()),
            "policyPackRef": None,
            "policyPackHash": None,
            "secretsRequired": [],
            "upstreamArtifacts": {
                "workspaceInventoryRef": None,
                "lockVerificationRef": None,
                "protocolCompatibilityRef": str(demo_path.resolve()),
                "taskRunRefs": [],
            },
        },
    }

    run_path = out_dir / "run-artifact.json"
    replay_path = out_dir / "replay-artifact.json"
    session_path = out_dir / "session-artifact.json"
    manifest_path = out_dir / "emvi-proof-slice-bridge-manifest.json"

    session_artifact = {
        "kind": "SessionArtifact",
        "bundle": bundle,
        "capturedAt": captured_at,
        "sessionRef": session_ref,
        "status": status,
        "receiptRef": receipt_ref,
        "runArtifactRef": str(run_path.resolve()),
        "replayArtifactRef": str(replay_path.resolve()),
    }

    manifest = {
        "kind": "EMVIProofSliceBridgeManifest",
        "generatedAt": captured_at,
        "sourceDemoArtifact": str(demo_path.resolve()),
        "sessionRef": session_ref,
        "receiptRef": receipt_ref,
        "bundle": bundle,
        "status": status,
        "files": {
            "runArtifact": str(run_path.resolve()),
            "replayArtifact": str(replay_path.resolve()),
            "sessionArtifact": str(session_path.resolve()),
        },
    }

    write_json(run_path, run_artifact)
    write_json(replay_path, replay_artifact)
    write_json(session_path, session_artifact)
    write_json(manifest_path, manifest)

    print(f"[emvi-bridge] OK: wrote {run_path}")
    print(f"[emvi-bridge] OK: wrote {replay_path}")
    print(f"[emvi-bridge] OK: wrote {session_path}")
    print(f"[emvi-bridge] OK: wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
