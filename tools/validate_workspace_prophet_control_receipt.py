#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "receipts" / "workspace-prophet-control-receipt.fixture-valid.json"

REQUIRED_BLOCKS = {
    "production_ready",
    "remote_execution",
    "autonomous_remediation",
    "customer_facing_claim",
}

REQUIRED_REPOS = {
    "SocioProphet/prophet-core-contracts",
    "SocioProphet/prophet-platform",
    "SocioProphet/sherlock-search",
    "SocioProphet/sociosphere",
    "SocioProphet/agentplane",
}

def main() -> int:
    try:
        record = json.loads(FIXTURE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERR: failed to load fixture: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    if record.get("schemaVersion") != "agentplane.workspace-prophet-control-receipt.v0.1":
        errors.append("schemaVersion mismatch")
    if record.get("recordType") != "WorkspaceProphetControlReceipt":
        errors.append("recordType mismatch")

    control = record.get("control_decision", {})
    if control.get("state") != "fixture_validated":
        errors.append("control_decision.state must be fixture_validated")
    if control.get("production_ready") is not False:
        errors.append("production_ready must be false")
    missing_blocks = sorted(REQUIRED_BLOCKS - set(control.get("blocked_actions", [])))
    if missing_blocks:
        errors.append(f"missing blocked actions: {missing_blocks}")

    placement = record.get("placement_decision", {})
    if placement.get("execution_location") != "local":
        errors.append("execution_location must be local for this fixture")
    if placement.get("cloud_burst_enabled") is not False:
        errors.append("cloud_burst_enabled must be false")
    if placement.get("authority_band") not in {"observe", "recommend", "queue"}:
        errors.append("authority_band must not grant execution")

    run_binding = record.get("run_binding", {})
    if run_binding.get("mode") != "fixture_only":
        errors.append("run_binding.mode must be fixture_only")
    if run_binding.get("runtime_execution") is not False:
        errors.append("runtime_execution must be false")

    missing_repos = sorted(REQUIRED_REPOS - set(record.get("source_repos", [])))
    if missing_repos:
        errors.append(f"missing source repos: {missing_repos}")

    for fragment in (
        "prophet-core-contracts:make validate",
        "prophet-platform:make validate-workspace-prophet-membrane-e2e",
        "sherlock-search:make validate-workspace-prophet-evidence-index",
        "sociosphere:python3 tools/validate_workspace_prophet_readiness.py",
    ):
        if fragment not in record.get("validation_refs", []):
            errors.append(f"missing validation ref: {fragment}")

    if not str(record.get("receipt_hash", "")).startswith("sha256:"):
        errors.append("receipt_hash must start with sha256:")

    if errors:
        print("ERR: Workspace PROPHET control receipt validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    print("OK: Workspace PROPHET control receipt fixture passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
