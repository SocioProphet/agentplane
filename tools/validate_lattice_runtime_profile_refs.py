#!/usr/bin/env python3
"""Validate AgentPlane Lattice runtime profile refs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "lattice-data-governai" / "runtime-profile-refs.v0.1.json"
NOTEBOOK = "runtime-asset:prophet-python-ml:0.1.0"
RAY = "runtime-asset:prophet-ray-ml:0.1.0"
BEAM = "runtime-asset:prophet-beam-dataops:0.1.0"

REQUIRED_ROLE_BINDINGS = {
    "NotebookSession": NOTEBOOK,
    "QueryRun": NOTEBOOK,
    "PublicationArtifact": NOTEBOOK,
    "ModelZooEntry": RAY,
    "ModelRuntimeProfile": RAY,
    "ModelEndpoint": RAY,
    "RayJobDryRunPlan": RAY,
    "RAGPipeline": RAY,
    "EvaluationBundle": RAY,
    "BeamPipelineDryRunPlan": BEAM,
    "TrainingDatasetRecipe": BEAM,
    "QualityProfile": BEAM,
    "VectorIndex": BEAM,
}


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    if not FIXTURE.exists():
        return fail(f"missing {FIXTURE}")
    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        require(data.get("apiVersion") == "agentplane.socioprophet.dev/v0", "apiVersion mismatch")
        require(data.get("kind") == "LatticeRuntimeProfileRefsFixture", "kind mismatch")
        refs = data.get("runtimeRefs")
        require(isinstance(refs, dict), "runtimeRefs must be object")
        require(refs.get("notebookRuntimeRef") == NOTEBOOK, "notebookRuntimeRef mismatch")
        require(refs.get("rayRuntimeRef") == RAY, "rayRuntimeRef mismatch")
        require(refs.get("beamRuntimeRef") == BEAM, "beamRuntimeRef mismatch")

        role_bindings = data.get("roleBindings")
        require(isinstance(role_bindings, dict), "roleBindings must be object")
        for role, runtime_ref in REQUIRED_ROLE_BINDINGS.items():
            require(role_bindings.get(role) == runtime_ref, f"roleBindings.{role} mismatch")

        overlay = data.get("runArtifactBindingOverlay")
        require(isinstance(overlay, dict), "runArtifactBindingOverlay must be object")
        bindings = overlay.get("sourceosBindings")
        require(isinstance(bindings, dict), "overlay sourceosBindings must be object")
        require(bindings.get("role") == "lattice-runtime-profile-consumer", "overlay role mismatch")
        require(bindings.get("mustNotOwnCanonicalSchemas") is True, "mustNotOwnCanonicalSchemas must be true")
        require(bindings.get("notebookRuntimeRef") == NOTEBOOK, "overlay notebookRuntimeRef mismatch")
        require(bindings.get("rayRuntimeRef") == RAY, "overlay rayRuntimeRef mismatch")
        require(bindings.get("beamRuntimeRef") == BEAM, "overlay beamRuntimeRef mismatch")
        task_refs = bindings.get("taskRuntimeRefs")
        require(isinstance(task_refs, dict), "taskRuntimeRefs must be object")
        require(task_refs.get("rayjob:community-truth-demo-train:0001") == RAY, "Ray task runtime mismatch")
        require(task_refs.get("beam:community-truth-demo-quality:0001") == BEAM, "Beam task runtime mismatch")

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
