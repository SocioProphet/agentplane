from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_sourceos_bundle import validate_bundle  # noqa: E402


def _valid_bundle() -> dict:
    return {
        "apiVersion": "agentplane.socioprophet.org/v0.1",
        "kind": "Bundle",
        "metadata": {
            "name": "sourceos-image-production-test",
            "version": "0.1.0",
            "createdAt": "2026-06-16T00:00:00Z",
            "licensePolicy": {"allowAGPL": False},
            "source": {"git": {"rev": "abc1234def5678"}},
        },
        "spec": {
            "policy": {
                "lane": "staging",
                "humanGateRequired": True,
                "maxRunSeconds": 120,
                "policyPackRef": "policy-packs/sourceos/image-production-staging",
                "policyPackHash": "deadbeef",
                "failOnTimeout": True,
            },
            "sourceos": {
                "artifactTruthRef": "SociOS-Linux/SourceOS:docs/ARTIFACT_TRUTH.md",
                "flavorRef": "SociOS-Linux/SourceOS:flavors/sourceos-workstation.example.yaml",
            },
            "secrets": {
                "required": ["KATELLO_CLI_USERNAME_FILE", "KATELLO_CLI_PASSWORD_FILE"],
                "secretRefRoot": "secrets://sourceos/katello",
            },
            "outputs": {
                "evidenceBundleRef": "urn:srcos:evidence-bundle:test",
            },
        },
    }


def _check(bundle: dict, bundle_dir: Path | None = None) -> dict:
    return validate_bundle(bundle, bundle_dir or Path("."))


def _blocks(result: dict) -> list[str]:
    return [f["condition"] for f in result["findings"] if f["severity"] == "block"]


def _warns(result: dict) -> list[str]:
    return [f["condition"] for f in result["findings"] if f["severity"] == "warn"]


# ── happy path ─────────────────────────────────────────────────────────────


def test_valid_bundle_passes() -> None:
    result = _check(_valid_bundle())
    assert result["ok"] is True
    assert _blocks(result) == []


# ── license ────────────────────────────────────────────────────────────────


def test_allow_agpl_true_blocks() -> None:
    b = _valid_bundle()
    b["metadata"]["licensePolicy"]["allowAGPL"] = True
    result = _check(b)
    assert "license_policy.allowAGPL" in _blocks(result)


def test_allow_agpl_missing_blocks() -> None:
    b = _valid_bundle()
    del b["metadata"]["licensePolicy"]["allowAGPL"]
    result = _check(b)
    assert "license_policy.allowAGPL" in _blocks(result)


# ── git rev ────────────────────────────────────────────────────────────────


def test_rev_unset_is_warn_not_block() -> None:
    b = _valid_bundle()
    b["metadata"]["source"]["git"]["rev"] = "UNSET"
    result = _check(b)
    assert result["ok"] is True
    assert "metadata.source.git.rev" in _warns(result)
    assert "metadata.source.git.rev" not in _blocks(result)


def test_rev_missing_blocks() -> None:
    b = _valid_bundle()
    del b["metadata"]["source"]["git"]["rev"]
    result = _check(b)
    assert "metadata.source.git.rev" in _blocks(result)


# ── sourceos ───────────────────────────────────────────────────────────────


def test_missing_artifact_truth_ref_blocks() -> None:
    b = _valid_bundle()
    del b["spec"]["sourceos"]["artifactTruthRef"]
    result = _check(b)
    assert "spec.sourceos.artifactTruthRef" in _blocks(result)


def test_missing_sourceos_block_blocks() -> None:
    b = _valid_bundle()
    del b["spec"]["sourceos"]
    result = _check(b)
    assert "spec.sourceos.artifactTruthRef" in _blocks(result)


# ── policy ─────────────────────────────────────────────────────────────────


def test_invalid_lane_blocks() -> None:
    b = _valid_bundle()
    b["spec"]["policy"]["lane"] = "development"
    result = _check(b)
    assert "spec.policy.lane" in _blocks(result)


def test_prod_lane_is_valid() -> None:
    b = _valid_bundle()
    b["spec"]["policy"]["lane"] = "prod"
    result = _check(b)
    assert "spec.policy.lane" not in _blocks(result)


def test_policy_pack_ref_unset_is_warn() -> None:
    b = _valid_bundle()
    b["spec"]["policy"]["policyPackRef"] = "UNSET"
    result = _check(b)
    assert result["ok"] is True
    assert "spec.policy.policyPackRef" in _warns(result)


def test_human_gate_missing_blocks() -> None:
    b = _valid_bundle()
    del b["spec"]["policy"]["humanGateRequired"]
    result = _check(b)
    assert "spec.policy.humanGateRequired" in _blocks(result)


# ── secrets ────────────────────────────────────────────────────────────────


def test_missing_secrets_required_blocks() -> None:
    b = _valid_bundle()
    del b["spec"]["secrets"]["required"]
    result = _check(b)
    assert "spec.secrets.required" in _blocks(result)


def test_empty_secrets_required_blocks() -> None:
    b = _valid_bundle()
    b["spec"]["secrets"]["required"] = []
    result = _check(b)
    assert "spec.secrets.required" in _blocks(result)


def test_inline_secret_value_blocks() -> None:
    b = _valid_bundle()
    b["spec"]["secrets"]["value"] = "supersecret"
    result = _check(b)
    assert "spec.secrets.inline" in _blocks(result)


# ── sociosAutomation ───────────────────────────────────────────────────────


def test_socios_automation_missing_tekton_ref_blocks() -> None:
    b = _valid_bundle()
    b["spec"]["sociosAutomation"] = {
        "katelloProduct": "SourceOS",
        "katelloRepository": "sourceos-live-iso",
        "katelloLifecycleEnvironment": "qa",
    }
    result = _check(b)
    assert "spec.sociosAutomation.tektonPipelineRef" in _blocks(result)


def test_socios_automation_fully_populated_passes() -> None:
    b = _valid_bundle()
    b["spec"]["sociosAutomation"] = {
        "tektonPipelineRef": "SociOS-Linux/socios:pipelines/tekton/pipeline-customize-live-iso.yaml",
        "katelloProduct": "SourceOS",
        "katelloRepository": "sourceos-live-iso",
        "katelloLifecycleEnvironment": "qa",
    }
    result = _check(b)
    assert all("sociosAutomation" not in c for c in _blocks(result))


# ── outputs ────────────────────────────────────────────────────────────────


def test_no_outputs_blocks() -> None:
    b = _valid_bundle()
    del b["spec"]["outputs"]
    result = _check(b)
    assert "spec.outputs" in _blocks(result)


def test_all_outputs_unset_blocks() -> None:
    b = _valid_bundle()
    b["spec"]["outputs"] = {
        "releaseSetRef": "UNSET",
        "bootReleaseSetRef": "UNSET",
    }
    result = _check(b)
    assert "spec.outputs" in _blocks(result)


def test_one_real_output_ref_passes() -> None:
    b = _valid_bundle()
    b["spec"]["outputs"] = {"katelloContentRef": "katello://SourceOS/SourceOS Recovery/sourceos-live.iso@sha256:abc"}
    result = _check(b)
    assert "spec.outputs" not in _blocks(result)


# ── smoke script ───────────────────────────────────────────────────────────


def test_smoke_script_exists_passes(tmp_path: Path) -> None:
    script = tmp_path / "smoke.sh"
    script.write_text("#!/bin/bash\n")
    b = _valid_bundle()
    b["spec"]["smoke"] = {"script": "smoke.sh"}
    result = validate_bundle(b, tmp_path)
    assert "spec.smoke.script" not in _blocks(result)


def test_smoke_script_missing_blocks(tmp_path: Path) -> None:
    b = _valid_bundle()
    b["spec"]["smoke"] = {"script": "nonexistent.sh"}
    result = validate_bundle(b, tmp_path)
    assert "spec.smoke.script" in _blocks(result)
