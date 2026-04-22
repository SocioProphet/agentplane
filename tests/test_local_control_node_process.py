from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from process_local_control_node_input import main as process_main


def test_process_local_control_node_input(tmp_path: Path, monkeypatch, capsys) -> None:
    payload = {
        "controlNodeProfileRef": "urn:srcos:control-node:test",
        "nodeCommanderRuntimeRef": "urn:srcos:node-commander:test",
        "candidateBuildRef": "urn:srcos:build:test",
        "targetImageRef": "urn:srcos:image:test",
        "promotionGateRef": "urn:srcos:image-gate:test",
        "validationEvidenceBundleRef": "urn:srcos:build-evidence:test",
        "scenarioResults": [
            {
                "scenarioId": "scenario.one",
                "status": "passed",
                "artifactRef": "urn:agentplane:artifact:validation:one"
            }
        ],
        "expectedAgentplaneOutputs": {
            "validationArtifact": "urn:agentplane:artifact:validation:test",
            "placementDecision": "urn:agentplane:placement:test",
            "runArtifact": "urn:agentplane:artifact:run:test",
            "replayArtifact": "urn:agentplane:artifact:replay:test"
        }
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    outdir = tmp_path / "artifacts"

    monkeypatch.setattr(sys, "argv", [
        "process_local_control_node_input.py",
        str(input_path),
        str(outdir),
    ])

    rc = process_main()
    assert rc == 0
    assert (outdir / "local-control-node-binding-artifact.json").exists()
    assert (outdir / "local-control-node-receipt.json").exists()

    summary = json.loads(capsys.readouterr().out)
    assert summary["kind"] == "LocalControlNodeProcessSummary"
    assert summary["result"] == "pass"
