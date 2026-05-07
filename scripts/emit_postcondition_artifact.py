#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"[postcondition-artifact] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"invalid bundle json: {e}", 2)


def split_env_list(name: str) -> list[str]:
    raw = os.getenv(name) or ""
    return [part.strip() for part in raw.split(",") if part.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_postcondition_artifact")
    ap.add_argument("bundle", help="path to bundle.json")
    ap.add_argument("run_artifact_ref", help="reference to run-artifact.json")
    ap.add_argument("--expected-state-hash", required=True)
    ap.add_argument("--observed-state-hash", required=True)
    ap.add_argument(
        "--comparison-result",
        default="UNKNOWN",
        choices=["MATCH", "PARTIAL_MISMATCH", "FAIL", "UNKNOWN"],
    )
    ap.add_argument("--matched-condition", action="append", dest="matched_conditions", default=[])
    ap.add_argument("--failed-condition", action="append", dest="failed_conditions", default=[])
    ap.add_argument("--evidence-ref", action="append", dest="evidence_refs", default=[])
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
        "kind": "PostconditionArtifact",
        "bundle": f"{name}@{ver}",
        "capturedAt": now_iso(),
        "runArtifactRef": args.run_artifact_ref,
        "planCommitRef": os.getenv("PLANNER_PLAN_COMMIT_REF") or "planning://plan-commit/UNKNOWN",
        "expectedStateHash": args.expected_state_hash,
        "observedStateHash": args.observed_state_hash,
        "comparisonResult": args.comparison_result,
        "verificationMode": os.getenv("PLANNER_VERIFICATION_MODE", "NONE"),
        "matchedConditions": args.matched_conditions,
        "failedConditions": args.failed_conditions,
        "counterexampleRefs": split_env_list("PLANNER_COUNTEREXAMPLE_REFS"),
        "evidenceRefs": args.evidence_refs,
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "postcondition-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[postcondition-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
