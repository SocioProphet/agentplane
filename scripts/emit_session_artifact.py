#!/usr/bin/env python3
"""Emit a SessionArtifact into the bundle artifacts directory.

Usage:
  scripts/emit_session_artifact.py <bundle.json> <session-ref> <status> [--receipt-ref <urn>] [--run-artifact-ref <path>] [--replay-artifact-ref <path>]
"""
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"[session-artifact] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"invalid bundle json: {e}", 2)


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_session_artifact")
    ap.add_argument("bundle")
    ap.add_argument("session_ref")
    ap.add_argument("status", choices=["success", "failure", "paused", "deferred", "canceled"])
    ap.add_argument("--receipt-ref", default=None)
    ap.add_argument("--run-artifact-ref", default=None)
    ap.add_argument("--replay-artifact-ref", default=None)
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
    artifact = {
        "kind": "SessionArtifact",
        "bundle": f"{name}@{ver}",
        "capturedAt": now_iso(),
        "sessionRef": args.session_ref,
        "status": args.status,
        "receiptRef": args.receipt_ref,
        "runArtifactRef": args.run_artifact_ref,
        "replayArtifactRef": args.replay_artifact_ref,
        "governanceContext": (spec.get("governanceContext") or None),
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "session-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[session-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
