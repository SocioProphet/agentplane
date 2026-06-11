#!/usr/bin/env python3
"""Run all PROMETHEUS SR validation checks: gate policy, replay refs, run artifacts."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SR = ROOT / "tests" / "fixtures" / "symbolic-regression"
STORE = SR / "store"
TOOLS = ROOT / "tools"

errors: list[str] = []
results: list[bool] = []


def run(cmd: list[str], expect_invalid: bool = False, label: str = "") -> bool:
    result = subprocess.run(cmd, capture_output=True, text=True)
    ok = (result.returncode == 0)
    if not ok:
        errors.append(f"FAIL {label}: {result.stderr.strip() or result.stdout.strip()}")
    else:
        print(f"PASS {label}")
    results.append(ok)
    return ok


py = sys.executable

# Valid run artifact
run([py, str(TOOLS / "validate_sr_run_artifact.py"), str(SR / "sr-run-artifact.valid.json")],
    label="sr-run-artifact valid")

# Valid gate policy
run([py, str(TOOLS / "validate_sr_gate_policy.py"), str(SR / "sr-gate-policy.valid.json")],
    label="sr-gate-policy valid")

# Valid automated gate policy + evaluation
run([py, str(TOOLS / "validate_prometheus_automated_gate_policy.py"),
     "--policy", str(SR / "automated-gate-policy.valid.json"),
     "--evaluation", str(SR / "automated-gate-evaluation.valid.json")],
    label="prometheus automated-gate-policy valid")

# Reject: missing replay on proposal (unresolvable ref)
run([py, str(TOOLS / "validate_sr_replay_ref.py"),
     str(SR / "reject_missing_replay_on_proposal.proposal.json"),
     "--fixture-store", str(STORE), "--expect-invalid"],
    label="reject missing-replay-on-proposal")

# Reject fixtures: run artifact invalidations
for reject_path in sorted(SR.glob("reject_*.json")):
    if reject_path.name.endswith(".expected.json") or reject_path.name.endswith(".proposal.json"):
        continue
    run([py, str(TOOLS / "validate_sr_run_artifact.py"), str(reject_path), "--expect-invalid"],
        label=f"reject {reject_path.name}")

# Reject fixtures: gate policy invalidations
for reject_path in sorted(SR.glob("reject-sr-gate-policy-*.json")):
    run([py, str(TOOLS / "validate_sr_gate_policy.py"), str(reject_path), "--expect-invalid"],
        label=f"reject {reject_path.name}")

# SINDy control-authority false guarantee (reject-sindy-control-authority-true)
run([py, str(TOOLS / "validate_sr_gate_policy.py"),
     str(SR / "reject-sindy-control-authority-true.json"), "--expect-invalid"],
    label="reject sindy-control-authority-true")

passed = sum(results)
if errors:
    print(file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    print(f"\n{passed} passed, {len(errors)} failed", file=sys.stderr)
    sys.exit(1)

print(f"\n{passed} PROMETHEUS SR checks passed")
