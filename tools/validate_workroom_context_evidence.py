#!/usr/bin/env python3
"""Validate WorkroomContextEvidence example."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/workroom-context-evidence.schema.v0.1.json"
EXAMPLE = ROOT / "examples/receipts/workroom-context-evidence.example.json"


def main():
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        for key in schema["required"]:
            if key not in example:
                raise AssertionError(f"missing {key}")
        assert example["kind"] == "WorkroomContextEvidence"
        assert example["workroomRef"].startswith("workroom://")
        assert example["contextGraphRef"]
        assert example["agentPlaneRefs"]["bundleRef"]
        assert example["agentPlaneRefs"]["runRef"]
        assert example["agentPlaneRefs"]["replayRef"]
        assert example["platformRefs"]["eventEnvelopeRefs"]
        assert example["platformRefs"]["evidenceReceiptRefs"]
    except Exception as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2
    print("OK: WorkroomContextEvidence validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
