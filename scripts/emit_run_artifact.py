#!/usr/bin/env python3
"""Emit a RunArtifact into the bundle artifacts directory.

This is the downstream evidence layer that complements:
- scripts/validate_bundle.py -> validation-artifact.json
- scripts/select-executor.py -> PlacementDecision (stdout)

Usage:
  scripts/emit_run_artifact.py <bundle.json> <executor-name> <exit-code> [--stdout <path>] [--stderr <path>]

Notes:
- This script does not execute the bundle. It records the outcome of a run performed by a runner backend.
- Upstream workspace artifacts (from sociosphere) may be referenced via optional env vars.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"[run-artifact] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"invalid bundle json: {e}", 2)


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_run_artifact")
    ap.add_argument("bundle", help="path to bundle.json")
    ap.add_argument("executor", help="chosen executor name")
    ap.add_argument("exit_code", type=int, help="exit code from the run")
    ap.add_argument("--stdout", dest="stdout_ref", default=None)
    ap.add_argument("--stderr", dest="stderr_ref", default=None)
    ap.add_argument("--bundle-path", dest="bundle_path", default=None)
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

    lane = (spec.get("policy") or {}).get("lane")
    backend = ((spec.get("vm") or {}).get("backendIntent"))
    if not lane or not backend:
        die("bundle spec.policy.lane and spec.vm.backendIntent are required", 2)

    status = "success" if args.exit_code == 0 else "failure"

    upstream = {
        "workspaceInventoryRef": os.getenv("SOCIOSPHERE_WORKSPACE_INVENTORY_REF"),
        "lockVerificationRef": os.getenv("SOCIOSPHERE_LOCK_VERIFICATION_REF"),
        "protocolCompatibilityRef": os.getenv("SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF"),
        "taskRunRefs": [p for p in (os.getenv("SOCIOSPHERE_TASK_RUN_REFS") or "").split(",") if p],
    }

    artifact = {
        "kind": "RunArtifact",
        "bundle": f"{name}@{ver}",
        "bundlePath": args.bundle_path,
        "capturedAt": now_iso(),
        "lane": lane,
        "executor": args.executor,
        "backendIntent": backend,
        "status": status,
        "exitCode": int(args.exit_code),
        "stdoutRef": args.stdout_ref,
        "stderrRef": args.stderr_ref,
        "upstreamArtifacts": upstream,
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "run-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[run-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
