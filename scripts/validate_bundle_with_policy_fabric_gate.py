#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from evaluate_policy_fabric_verdict_envelope import (
    VerdictEnvelopeError,
    evaluate_verdict_envelope,
    write_gate_artifact,
)


def die(msg: str, code: int = 2) -> None:
    print(f"[validate+policy-fabric] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bundle validation and optional Policy Fabric verdict gating.")
    parser.add_argument("bundle_json", help="Path to bundle.json")
    parser.add_argument("--verdict-envelope", default=None, help="Optional path to Policy Fabric verdict envelope JSON")
    parser.add_argument("--require-verdict-envelope", action="store_true", help="Fail closed if verdict envelope is missing")
    args = parser.parse_args()

    bundle_path = Path(args.bundle_json)
    if not bundle_path.exists():
        die(f"bundle not found: {bundle_path}")

    validate_script = Path(__file__).with_name("validate_bundle.py")
    result = subprocess.run([sys.executable, str(validate_script), str(bundle_path)])
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    verdict_path_str = args.verdict_envelope or os.environ.get("POLICY_FABRIC_VERDICT_ENVELOPE")
    if not verdict_path_str:
        if args.require_verdict_envelope:
            die("verdict envelope required but not provided")
        print("[validate+policy-fabric] OK: core bundle validation passed; no verdict envelope provided")
        return 0

    verdict_path = Path(verdict_path_str)
    bundle = _load_json(bundle_path)
    out_dir = Path(bundle["spec"]["artifacts"]["outDir"])
    gate_artifact_path = out_dir / "policy-fabric-verdict-gate-artifact.json"

    try:
        artifact = evaluate_verdict_envelope(verdict_path)
        write_gate_artifact(artifact, gate_artifact_path)
    except VerdictEnvelopeError as e:
        die(str(e), 2)

    if artifact["result"] != "allow":
        die(
            f"policy fabric verdict denied bundle: domain={artifact['domain']} fit={artifact['fit']} failedPredicates={artifact['failedPredicates']}",
            2,
        )

    print(f"[validate+policy-fabric] OK: wrote {gate_artifact_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
