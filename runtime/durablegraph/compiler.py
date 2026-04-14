from __future__ import annotations

from pathlib import Path

from .control_pin import validate_control_pin
from .envelope import ControlPin, DurableGraphEnvelope, ExecutionPayload, UpstreamArtifacts
from .protocol import GraphNode, RetryPolicy, StoreConfig


def graph_name_for_bundle(bundle_ref: str, lane: str) -> str:
    return f"{bundle_ref.replace('@', '.').replace('/', '.').replace(':', '.')}.lane.{lane}"


def compile_bundle_to_graph(
    *,
    repo_root: Path,
    run_id: str,
    lane: str,
    bundle_ref: str,
    bundle_rev: str | None,
    executor_ref: str,
    policy_pack_ref: str | None,
    policy_pack_hash: str | None,
    backend_intent: str,
    module_path: str,
    smoke_script: str,
    artifact_dir: str,
    max_run_seconds: int,
    upstream: UpstreamArtifacts,
) -> tuple[dict, DurableGraphEnvelope]:
    manifest = validate_control_pin(repo_root)

    envelope = DurableGraphEnvelope(
        run_id=run_id,
        lane=lane,
        bundle_ref=bundle_ref,
        bundle_rev=bundle_rev,
        executor_ref=executor_ref,
        policy_pack_ref=policy_pack_ref,
        policy_pack_hash=policy_pack_hash,
        upstream_artifacts=upstream,
        payload=ExecutionPayload(
            backend_intent=backend_intent,
            module_path=module_path,
            smoke_script=smoke_script,
            artifact_dir=artifact_dir,
            max_run_seconds=max_run_seconds,
        ),
        control_pin=ControlPin(
            canonical_repository=manifest.canonical_repository,
            canonical_package_path=manifest.canonical_package_path,
            canonical_schema_path=manifest.canonical_schema_path,
            version=manifest.version,
            manifest_ref="policy/imports/control-matrix/manifest.json",
        ),
    )

    graph = {
        "graph_name": graph_name_for_bundle(bundle_ref=bundle_ref, lane=lane),
        "nodes": [
            GraphNode(
                node_name="APControlGateNode",
                namespace="agentplane",
                identifier="control_gate",
                inputs={"meta_json": ""},
                next_nodes=["exec_bundle"],
            ).model_dump(),
            GraphNode(
                node_name="APExecNode",
                namespace="agentplane",
                identifier="exec_bundle",
                inputs={"meta_json": "${{ control_gate.outputs.meta_json }}"},
                next_nodes=["emit_evidence"],
            ).model_dump(),
            GraphNode(
                node_name="APEvidenceNode",
                namespace="agentplane",
                identifier="emit_evidence",
                inputs={
                    "meta_json": "${{ exec_bundle.outputs.meta_json }}",
                    "exec_json": "${{ exec_bundle.outputs.exec_json }}",
                },
                next_nodes=[],
            ).model_dump(),
        ],
        "retry_policy": RetryPolicy(max_retries=0).model_dump(),
        "store_config": StoreConfig(
            required_keys=["run_id", "bundle_ref", "artifact_dir", "lane", "executor_ref"],
            default_values={
                "run_id": run_id,
                "bundle_ref": bundle_ref,
                "artifact_dir": artifact_dir,
                "lane": lane,
                "executor_ref": executor_ref,
            },
        ).model_dump(),
    }

    return graph, envelope
