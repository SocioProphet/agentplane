#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = [
    "controlNodeProfileRef",
    "nodeCommanderRuntimeRef",
    "candidateBuildRef",
    "targetImageRef",
    "promotionGateRef",
    "validationEvidenceBundleRef",
    "scenarioResults",
    "expectedAgentplaneOutputs",
]

REQUIRED_SCENARIO_FIELDS = ["scenarioId", "status", "artifactRef"]
REQUIRED_OUTPUT_FIELDS = ["validationArtifact", "placementDecision", "runArtifact", "replayArtifact"]


def die(msg: str, code: int = 2) -> None:
    print(f"[local-control-node] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    if len(sys.argv) not in (2, 3):
        die("usage: scripts/validate_local_control_node_input.py <input.json> [outdir]", 2)

    input_path = Path(sys.argv[1])
    outdir = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    if not input_path.exists():
        die(f"input not found: {input_path}", 2)

    with input_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            die(f"invalid JSON: {e}", 2)

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            die(f"missing required field: {key}", 2)

    if not isinstance(data["scenarioResults"], list) or not data["scenarioResults"]:
        die("scenarioResults must be a non-empty array", 2)

    for idx, item in enumerate(data["scenarioResults"]):
        for key in REQUIRED_SCENARIO_FIELDS:
            if key not in item:
                die(f"scenarioResults[{idx}] missing required field: {key}", 2)

    outputs = data["expectedAgentplaneOutputs"]
    for key in REQUIRED_OUTPUT_FIELDS:
        if key not in outputs:
            die(f"expectedAgentplaneOutputs missing required field: {key}", 2)

    artifact = {
        "kind": "LocalControlNodeBindingArtifact",
        "validatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "inputPath": os.path.abspath(str(input_path)),
        "result": "pass",
        "consumedRefs": {
            "controlNodeProfileRef": data["controlNodeProfileRef"],
            "nodeCommanderRuntimeRef": data["nodeCommanderRuntimeRef"],
            "candidateBuildRef": data["candidateBuildRef"],
            "promotionGateRef": data["promotionGateRef"],
            "validationEvidenceBundleRef": data["validationEvidenceBundleRef"],
        },
        "expectedAgentplaneOutputs": outputs,
        "scenarioCount": len(data["scenarioResults"]),
    }

    if outdir is None:
        print(json.dumps(artifact, indent=2, sort_keys=True))
        return 0

    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / "local-control-node-binding-artifact.json"
    with outpath.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, sort_keys=True)
    print(f"[local-control-node] OK: wrote {outpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
