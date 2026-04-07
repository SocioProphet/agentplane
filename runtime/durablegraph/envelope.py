from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UpstreamArtifacts(BaseModel):
    workspace_inventory_ref: str | None = None
    lock_verification_ref: str | None = None
    protocol_compatibility_ref: str | None = None
    task_run_refs: list[str] = Field(default_factory=list)


class ExecutionPayload(BaseModel):
    backend_intent: str
    module_path: str
    smoke_script: str
    artifact_dir: str
    max_run_seconds: int


class ControlPin(BaseModel):
    canonical_repository: str
    canonical_package_path: str
    canonical_schema_path: str
    version: str
    manifest_ref: str


class DurableGraphEnvelope(BaseModel):
    version: Literal["agentplane.durablegraph.v1"] = "agentplane.durablegraph.v1"
    run_id: str
    lane: str
    bundle_ref: str
    bundle_rev: str | None = None
    executor_ref: str
    policy_pack_ref: str | None = None
    policy_pack_hash: str | None = None
    upstream_artifacts: UpstreamArtifacts = Field(default_factory=UpstreamArtifacts)
    payload: ExecutionPayload
    control_pin: ControlPin
