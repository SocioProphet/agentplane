from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_control_matrix_gate import evaluate_bundle_gate


def make_bundle(tmp_path: Path, lane: str, human_gate_required: bool) -> tuple[Path, dict]:
    out_dir = tmp_path / "artifacts"
    bundle = {
        "apiVersion": "agentplane.socioprophet.org/v0.1",
        "kind": "Bundle",
        "metadata": {
            "name": "gate-test",
            "version": "0.0.1",
            "createdAt": "2026-04-09T00:00:00Z",
            "licensePolicy": {"allowAGPL": False},
        },
        "spec": {
            "artifacts": {"outDir": str(out_dir)},
            "policy": {
                "lane": lane,
                "humanGateRequired": human_gate_required,
                "maxRunSeconds": 30,
            },
            "secrets": {"required": [], "secretRefRoot": "secrets://user"},
            "smoke": {"script": "bundles/example-agent/smoke.sh"},
            "vm": {"backendIntent": "lima-process", "modulePath": "bundles/example-agent/vm.nix"},
        },
    }
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return bundle_path, bundle


def write_policy_bundle(tmp_path: Path) -> Path:
    rows = [
        {
            "row_id": "R-HARDEN-STAGING",
            "policy_key": "R-HARDEN-STAGING|harden|policy↔action",
            "allow_if": {
                "phase": "harden",
                "authority": "constrained_action",
                "environment_tier": "staging",
                "approval_mode": "dual_control",
                "tenant_scope": "single_tenant",
            },
            "enforcement_point": "policy_engine",
            "control_type": "preventive",
            "runbook_id": "RB-001",
            "ship_blocker": "PASS",
        },
        {
            "row_id": "R-OPERATE-PROD",
            "policy_key": "R-OPERATE-PROD|operate|policy↔action",
            "allow_if": {
                "phase": "operate",
                "authority": "constrained_action",
                "environment_tier": "prod",
                "approval_mode": "dual_control",
                "tenant_scope": "single_tenant",
            },
            "enforcement_point": "policy_engine",
            "control_type": "preventive",
            "runbook_id": "RB-001",
            "ship_blocker": "PASS",
        },
    ]
    path = tmp_path / "compiled_policy_bundle_v3.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def test_staging_bundle_passes_first_policy_gate(tmp_path: Path) -> None:
    bundle_path, bundle = make_bundle(tmp_path, lane="staging", human_gate_required=False)
    policy_bundle = write_policy_bundle(tmp_path)

    artifact = evaluate_bundle_gate(bundle, bundle_path, policy_bundle)
    assert artifact["result"] == "allow"
    assert artifact["matchedRowIds"] == ["R-HARDEN-STAGING"]


def test_prod_autonomous_bundle_fails_closed_without_exact_policy_row(tmp_path: Path) -> None:
    bundle_path, bundle = make_bundle(tmp_path, lane="prod", human_gate_required=False)
    policy_bundle = write_policy_bundle(tmp_path)

    artifact = evaluate_bundle_gate(bundle, bundle_path, policy_bundle)
    assert artifact["result"] == "deny"
    assert artifact["reason"] == "no exact matching policy row"
    assert artifact["matchedRowIds"] == []
