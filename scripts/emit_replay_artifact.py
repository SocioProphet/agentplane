#!/usr/bin/env python3
"""Emit a ReplayArtifact into the bundle artifacts directory.

Usage:
  scripts/emit_replay_artifact.py <bundle.json> <executor-name> [--bundle-rev <sha>] [--bundle-path <path>]

This artifact records the minimum inputs needed to replay a run deterministically:
- bundle path + rev (when available)
- artifact directory
- policy pack refs/hashes
- required secret refs (names only)
- optional upstream workspace artifact references
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"[replay-artifact] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"invalid bundle json: {e}", 2)


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_replay_artifact")
    ap.add_argument("bundle", help="path to bundle.json")
    ap.add_argument("executor", help="chosen executor name")
    ap.add_argument("--bundle-rev", default=None)
    ap.add_argument("--bundle-path", default=None)
    args = ap.parse_args()

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        die(f"bundle not found: {bundle_path}", 2)

    b = load_bundle(bundle_path)
    md = b.get("metadata") or {}
    spec = b.get("spec") or {}

    name = md.get("name")
    ver = md.get("version")
    if not name or not ver:
        die("bundle metadata.name and metadata.version are required", 2)

    out_dir = (spec.get("artifacts") or {}).get("outDir")
    if not out_dir:
        die("bundle spec.artifacts.outDir is required", 2)

    backend = ((spec.get("vm") or {}).get("backendIntent"))
    if not backend:
        die("bundle spec.vm.backendIntent is required", 2)

    pol = spec.get("policy") or {}
    secrets = spec.get("secrets") or {}

    upstream = {
        "workspaceInventoryRef": os.getenv("SOCIOSPHERE_WORKSPACE_INVENTORY_REF"),
        "lockVerificationRef": os.getenv("SOCIOSPHERE_LOCK_VERIFICATION_REF"),
        "protocolCompatibilityRef": os.getenv("SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF"),
        "taskRunRefs": [p for p in (os.getenv("SOCIOSPHERE_TASK_RUN_REFS") or "").split(",") if p],
    }

    artifact = {
        "kind": "ReplayArtifact",
        "bundle": f"{name}@{ver}",
        "capturedAt": now_iso(),
        "executor": args.executor,
        "backendIntent": backend,
        "inputs": {
            "bundlePath": args.bundle_path or str(bundle_path),
            "bundleRev": args.bundle_rev,
            "artifactDir": str(Path(out_dir).resolve()),
            "policyPackRef": pol.get("policyPackRef"),
            "policyPackHash": pol.get("policyPackHash"),
            "secretsRequired": secrets.get("required") or [],
            "upstreamArtifacts": upstream,
        },
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "replay-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[replay-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
