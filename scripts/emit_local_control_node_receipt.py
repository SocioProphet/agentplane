#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"[local-control-node-receipt] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    if len(sys.argv) != 3:
        die("usage: scripts/emit_local_control_node_receipt.py <binding-artifact.json> <outdir>", 2)

    artifact_path = Path(sys.argv[1])
    outdir = Path(sys.argv[2])

    if not artifact_path.exists():
        die(f"binding artifact not found: {artifact_path}", 2)

    with artifact_path.open("r", encoding="utf-8") as f:
        try:
            artifact = json.load(f)
        except json.JSONDecodeError as e:
            die(f"invalid JSON: {e}", 2)

    if artifact.get("kind") != "LocalControlNodeBindingArtifact":
        die("binding artifact kind must be LocalControlNodeBindingArtifact", 2)
    if artifact.get("result") != "pass":
        die("binding artifact result must be pass", 2)

    consumed = artifact.get("consumedRefs") or {}
    outputs = artifact.get("expectedAgentplaneOutputs") or {}

    receipt = {
        "kind": "LocalControlNodeReceipt",
        "issuedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "bindingArtifactRef": str(artifact_path.resolve()),
        "controlNodeProfileRef": consumed.get("controlNodeProfileRef"),
        "nodeCommanderRuntimeRef": consumed.get("nodeCommanderRuntimeRef"),
        "candidateBuildRef": consumed.get("candidateBuildRef"),
        "promotionGateRef": consumed.get("promotionGateRef"),
        "validationEvidenceBundleRef": consumed.get("validationEvidenceBundleRef"),
        "expectedAgentplaneOutputs": outputs,
        "result": "sealed",
    }

    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / "local-control-node-receipt.json"
    with outpath.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
    print(f"[local-control-node-receipt] OK: wrote {outpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
