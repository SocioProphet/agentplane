from __future__ import annotations

import json
from pathlib import Path

from runtime.durablegraph.compiler import compile_bundle_to_graph
from runtime.durablegraph.envelope import UpstreamArtifacts


MANIFEST = {
    "canonical_repository": "SocioProphet/socioprophet-standards-storage",
    "canonical_package_path": "examples/control-matrix/v3",
    "canonical_schema_path": "schemas/control-matrix",
    "version": "v3",
    "status": "seeded-import-lane",
    "expected_bundles": {
        "policy": "policy/imports/control-matrix/compiled_policy_bundle_v3.json",
        "monitor": "monitors/generated/control-matrix/compiled_monitor_bundle_v3.json",
        "test": "tests/generated/control-matrix/compiled_test_bundle_v3.json"
    }
}


def seed_control_import(repo_root: Path) -> None:
    manifest_path = repo_root / "policy/imports/control-matrix/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")

    for relpath in MANIFEST["expected_bundles"].values():
        target = repo_root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n", encoding="utf-8")


def test_compiler_roots_graph_at_control_gate(tmp_path: Path) -> None:
    seed_control_import(tmp_path)

    graph, envelope = compile_bundle_to_graph(
        repo_root=tmp_path,
        run_id="run-123",
        lane="staging",
        bundle_ref="example-agent@0.1.0",
        bundle_rev="abc123",
        executor_ref="lima-nixbuilder",
        policy_pack_ref="policy-packs/dev/default",
        policy_pack_hash="hash-1",
        backend_intent="lima-process",
        module_path="bundles/example-agent/vm.nix",
        smoke_script="bundles/example-agent/smoke.sh",
        artifact_dir="./artifacts/example-agent",
        max_run_seconds=20,
        upstream=UpstreamArtifacts(),
    )

    assert graph["nodes"][0]["identifier"] == "control_gate"
    assert graph["nodes"][1]["identifier"] == "exec_bundle"
    assert graph["nodes"][2]["identifier"] == "emit_evidence"
    assert graph["retry_policy"]["max_retries"] == 0
    assert graph["store_config"]["default_values"]["run_id"] == "run-123"
    assert envelope.control_pin.version == "v3"
    assert envelope.payload.backend_intent == "lima-process"
