#!/usr/bin/env python3
"""Emit postcondition and optional divergence evidence for a completed run.

This wrapper centralizes the runner-facing interface for execution evidence.
It intentionally delegates artifact shape to the narrower emitters added in the
postcondition/divergence tranche, so shell runners do not need to hand-author
canonical JSON.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


COMPARISON_RESULTS = {"MATCH", "PARTIAL_MISMATCH", "FAIL", "UNKNOWN"}
DIVERGENCE_CLASSES = {
    "STATE_MISMATCH",
    "POLICY_MISMATCH",
    "SIDE_EFFECT_MISMATCH",
    "EVIDENCE_STALENESS",
    "EXECUTION_FAILURE",
    "ABSTRACTION_FAILURE",
}


def die(message: str, code: int = 2) -> None:
    print(f"[execution-evidence] ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(cmd: list[str]) -> None:
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(prog="emit_execution_evidence_artifacts")
    parser.add_argument("bundle", help="path to bundle.json")
    parser.add_argument("run_artifact_ref", help="reference to run-artifact.json")
    parser.add_argument("--expected-state-hash", required=True)
    parser.add_argument("--observed-state-hash", required=True)
    parser.add_argument("--comparison-result", default="UNKNOWN", choices=sorted(COMPARISON_RESULTS))
    parser.add_argument("--matched-condition", action="append", default=[])
    parser.add_argument("--failed-condition", action="append", default=[])
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--divergence-class", choices=sorted(DIVERGENCE_CLASSES), default=None)
    parser.add_argument("--expected-ref", default=None)
    parser.add_argument("--observed-ref", default=None)
    parser.add_argument("--divergence-severity", default="HIGH", choices=["LOW", "MODERATE", "HIGH", "CRITICAL"])
    parser.add_argument("--policy-impact", default=None)
    parser.add_argument("--incident-ref", default=None)
    parser.add_argument("--replan-required", action="store_true")
    args = parser.parse_args()

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        die(f"bundle not found: {bundle_path}")

    script_dir = Path(__file__).resolve().parent
    postcondition = script_dir / "emit_postcondition_artifact.py"
    divergence = script_dir / "emit_divergence_artifact.py"
    if not postcondition.exists():
        die(f"missing postcondition emitter: {postcondition}")
    if args.divergence_class and not divergence.exists():
        die(f"missing divergence emitter: {divergence}")

    post_cmd = [
        sys.executable,
        str(postcondition),
        str(bundle_path),
        args.run_artifact_ref,
        "--expected-state-hash",
        args.expected_state_hash,
        "--observed-state-hash",
        args.observed_state_hash,
        "--comparison-result",
        args.comparison_result,
    ]
    for value in args.matched_condition:
        post_cmd.extend(["--matched-condition", value])
    for value in args.failed_condition:
        post_cmd.extend(["--failed-condition", value])
    for value in args.evidence_ref:
        post_cmd.extend(["--evidence-ref", value])
    run(post_cmd)

    should_emit_divergence = bool(args.divergence_class)
    if args.comparison_result in {"PARTIAL_MISMATCH", "FAIL"} and not args.divergence_class:
        die("divergence-class is required when comparison-result is PARTIAL_MISMATCH or FAIL")

    if should_emit_divergence:
        if not args.expected_ref or not args.observed_ref:
            die("expected-ref and observed-ref are required when emitting divergence")
        div_cmd = [
            sys.executable,
            str(divergence),
            str(bundle_path),
            args.run_artifact_ref,
            args.divergence_class,
            args.expected_ref,
            args.observed_ref,
            "--severity",
            args.divergence_severity,
        ]
        if args.policy_impact:
            div_cmd.extend(["--policy-impact", args.policy_impact])
        if args.incident_ref:
            div_cmd.extend(["--incident-ref", args.incident_ref])
        if args.replan_required:
            div_cmd.append("--replan-required")
        for value in args.evidence_ref:
            div_cmd.extend(["--evidence-ref", value])
        run(div_cmd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
