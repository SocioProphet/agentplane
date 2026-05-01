#!/usr/bin/env python3
"""Validate AgentPlane Lattice Data/GovernAI execution-ref fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-data-governai" / "execution-refs.v0.1.json"

REQUIRED_REFS = {
    "runtimeAssetRef": "runtime-asset:prophet-python-ml:0.1.0",
    "dataProductRef": "urn:srcos:data-product:community_truth_demo",
    "dataContractRef": "urn:srcos:data-contract:community_truth_demo",
    "modelAssetRef": "urn:srcos:model:community_truth_demo_candidate",
    "evaluationBundleRef": "urn:srcos:evaluation-bundle:community_truth_demo_model_eval",
    "factsheetRef": "urn:srcos:factsheet:community_truth_demo_model",
    "publicationArtifactRef": "urn:srcos:publication-artifact:community_truth_demo_report",
    "policyBundleRef": "urn:srcos:policy:mlops-governed-execution-demo",
    "topicScopeRef": "slash-topic://lattice/data-governai",
    "semanticMembraneRef": "newhope://membranes/lattice-data-governai-admission@0.1.0",
}
REQUIRED_SOURCE_REFS = {
    "schemaPr",
    "platformPr",
    "runtimePr",
    "mlopsPr",
    "policyPr",
    "topologyPr",
    "sherlockPr",
    "slashTopicsPr",
    "newHopePr",
}


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_list(mapping: dict[str, Any], key: str) -> list[Any]:
    value = mapping.get(key)
    require(isinstance(value, list), f"{key} must be a list")
    return value


def validate_lattice_refs(refs: dict[str, Any], *, allow_notebook: bool) -> None:
    require(refs.get("role") == "lattice-ref-consumer", "sourceosBindings.role must be lattice-ref-consumer")
    require(refs.get("mustNotOwnCanonicalSchemas") is True, "sourceosBindings.mustNotOwnCanonicalSchemas must be true")
    for key, expected in REQUIRED_REFS.items():
        require(refs.get(key) == expected, f"sourceosBindings.{key} mismatch")
    if allow_notebook:
        require(refs.get("notebookSessionRef") == "notebook-session:community-truth-demo", "notebookSessionRef mismatch")
        require(refs.get("queryRunRef") == "query-run:community-truth-demo:001", "queryRunRef mismatch")
        require(refs.get("topicPackRef") == "slash-topics://packs/lattice-data-governai@0.1.0", "topicPackRef mismatch")
    record_refs = require_list(refs, "platformAssetRecordRefs")
    for required in [
        "urn:srcos:data-product:community_truth_demo",
        "runtime-asset:prophet-python-ml:0.1.0",
        "urn:srcos:evaluation-bundle:community_truth_demo_model_eval",
        "urn:srcos:publication-artifact:community_truth_demo_report",
    ]:
        require(required in record_refs, f"platformAssetRecordRefs missing {required}")


def validate_run_artifact(run: dict[str, Any]) -> None:
    require(run.get("kind") == "RunArtifact", "runArtifact.kind must be RunArtifact")
    require(run.get("lane") == "staging", "runArtifact.lane must be staging")
    require(run.get("backendIntent") == "fleet", "runArtifact.backendIntent must be fleet")
    require(run.get("status") == "success", "runArtifact.status must be success")
    require(run.get("exitCode") == 0, "runArtifact.exitCode must be 0")
    upstream = run.get("upstreamArtifacts")
    require(isinstance(upstream, dict), "runArtifact.upstreamArtifacts must be object")
    tasks = require_list(upstream, "taskRunRefs")
    require("rayjob:community-truth-demo-train:0001" in tasks, "runArtifact must preserve Ray task ref")
    require("beam:community-truth-demo-quality:0001" in tasks, "runArtifact must preserve Beam task ref")
    bindings = run.get("sourceosBindings")
    require(isinstance(bindings, dict), "runArtifact.sourceosBindings must be object")
    validate_lattice_refs(bindings, allow_notebook=False)


def validate_replay_artifact(replay: dict[str, Any]) -> None:
    require(replay.get("kind") == "ReplayArtifact", "replayArtifact.kind must be ReplayArtifact")
    require(replay.get("backendIntent") == "fleet", "replayArtifact.backendIntent must be fleet")
    inputs = replay.get("inputs")
    require(isinstance(inputs, dict), "replayArtifact.inputs must be object")
    require(inputs.get("bundlePath") == "fixtures/lattice-data-governai/execution-refs.v0.1.json", "replay bundlePath mismatch")
    require(inputs.get("policyPackRef") == "SocioProphet/policy-fabric#39", "policyPackRef mismatch")
    require(inputs.get("secretsRequired") == [], "secretsRequired must be empty")
    upstream = inputs.get("upstreamArtifacts")
    require(isinstance(upstream, dict), "replay.inputs.upstreamArtifacts must be object")
    tasks = require_list(upstream, "taskRunRefs")
    require("rayjob:community-truth-demo-train:0001" in tasks, "replay must preserve Ray task ref")
    require("beam:community-truth-demo-quality:0001" in tasks, "replay must preserve Beam task ref")
    bindings = inputs.get("sourceosBindings")
    require(isinstance(bindings, dict), "replay.inputs.sourceosBindings must be object")
    validate_lattice_refs(bindings, allow_notebook=True)


def main() -> int:
    if not FIXTURE.exists():
        return fail(f"missing {FIXTURE}")
    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        require(isinstance(data, dict), "fixture root must be object")
        require(data.get("apiVersion") == "agentplane.socioprophet.dev/v0", "apiVersion mismatch")
        require(data.get("kind") == "LatticeDataGovernAIExecutionRefsFixture", "kind mismatch")
        source_refs = data.get("sourceRefs")
        require(isinstance(source_refs, dict), "sourceRefs must be object")
        missing = sorted(REQUIRED_SOURCE_REFS - set(source_refs))
        require(not missing, f"sourceRefs missing {missing}")
        lattice_refs = data.get("latticeRefs")
        require(isinstance(lattice_refs, dict), "latticeRefs must be object")
        for key, expected in REQUIRED_REFS.items():
            require(lattice_refs.get(key) == expected, f"latticeRefs.{key} mismatch")
        require(lattice_refs.get("topicPackRef") == "slash-topics://packs/lattice-data-governai@0.1.0", "latticeRefs.topicPackRef mismatch")
        validate_run_artifact(data.get("runArtifact", {}))
        validate_replay_artifact(data.get("replayArtifact", {}))
        safety = data.get("safety")
        require(isinstance(safety, dict), "safety must be object")
        require(safety.get("dryRunOnly") is True, "dryRunOnly must be true")
        require(safety.get("hostMutation") is False, "hostMutation must be false")
        require(safety.get("network") == "none", "network must be none")
        require(safety.get("secrets") == "none", "secrets must be none")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))
    print(f"PASS {FIXTURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
