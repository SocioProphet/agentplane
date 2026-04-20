from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from emit_local_control_node_receipt import main as emit_main


def test_emit_local_control_node_receipt(tmp_path: Path, monkeypatch) -> None:
    binding = {
        "kind": "LocalControlNodeBindingArtifact",
        "result": "pass",
        "consumedRefs": {
            "controlNodeProfileRef": "urn:srcos:control-node:test",
            "nodeCommanderRuntimeRef": "urn:srcos:node-commander:test",
            "candidateBuildRef": "urn:srcos:build:test",
            "promotionGateRef": "urn:srcos:image-gate:test",
            "validationEvidenceBundleRef": "urn:srcos:build-evidence:test",
        },
        "expectedAgentplaneOutputs": {
            "validationArtifact": "urn:agentplane:artifact:validation:test",
            "placementDecision": "urn:agentplane:placement:test",
            "runArtifact": "urn:agentplane:artifact:run:test",
            "replayArtifact": "urn:agentplane:artifact:replay:test",
        },
    }
    binding_path = tmp_path / "binding.json"
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    outdir = tmp_path / "artifacts"

    monkeypatch.setattr(sys, "argv", [
        "emit_local_control_node_receipt.py",
        str(binding_path),
        str(outdir),
    ])

    rc = emit_main()
    assert rc == 0

    outpath = outdir / "local-control-node-receipt.json"
    assert outpath.exists()
    receipt = json.loads(outpath.read_text(encoding="utf-8"))
    assert receipt["kind"] == "LocalControlNodeReceipt"
    assert receipt["result"] == "sealed"
    assert receipt["controlNodeProfileRef"] == "urn:srcos:control-node:test"
