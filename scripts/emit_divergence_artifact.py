#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

DIVERGENCE_CLASSES = [
    "STATE_MISMATCH",
    "POLICY_MISMATCH",
    "SIDE_EFFECT_MISMATCH",
    "EVIDENCE_STALENESS",
    "EXECUTION_FAILURE",
    "ABSTRACTION_FAILURE",
]
SEVERITIES = ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def die(msg: str, code: int = 2) -> None:
    print(f"[divergence-artifact] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"invalid bundle json: {e}", 2)


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_divergence_artifact")
    ap.add_argument("bundle", help="path to bundle.json")
    ap.add_argument("run_artifact_ref", help="reference to run-artifact.json")
    ap.add_argument("divergence_class", choices=DIVERGENCE_CLASSES)
    ap.add_argument("expected_ref")
    ap.add_argument("observed_ref")
    ap.add_argument("--severity", default="HIGH", choices=SEVERITIES)
    ap.add_argument("--policy-impact", default=None)
    ap.add_argument("--incident-ref", default=None)
    ap.add_argument("--replan-required", action="store_true")
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
        "kind": "DivergenceArtifact",
        "bundle": f"{name}@{ver}",
        "capturedAt": now_iso(),
        "runArtifactRef": args.run_artifact_ref,
        "planCommitRef": os.getenv("PLANNER_PLAN_COMMIT_REF") or "planning://plan-commit/UNKNOWN",
        "divergenceClass": args.divergence_class,
        "severity": args.severity,
        "expectedRef": args.expected_ref,
        "observedRef": args.observed_ref,
        "policyImpact": args.policy_impact,
        "incidentRef": args.incident_ref,
        "replanRequired": args.replan_required,
        "evidenceRefs": args.evidence_refs,
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "divergence-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[divergence-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
