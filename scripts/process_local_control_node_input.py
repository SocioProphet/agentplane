#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from validate_local_control_node_input import main as validate_main
from emit_local_control_node_receipt import main as emit_main


def die(msg: str, code: int = 2) -> None:
    print(f"[local-control-node-process] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    if len(sys.argv) != 3:
        die("usage: scripts/process_local_control_node_input.py <input.json> <outdir>", 2)

    input_path = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    # Step 1: validate and emit the binding artifact.
    sys.argv = [
        "validate_local_control_node_input.py",
        str(input_path),
        str(outdir),
    ]
    validate_main()

    binding_artifact = outdir / "local-control-node-binding-artifact.json"
    if not binding_artifact.exists():
        die("expected binding artifact was not emitted", 2)

    # Step 2: consume the binding artifact and emit the receipt.
    sys.argv = [
        "emit_local_control_node_receipt.py",
        str(binding_artifact),
        str(outdir),
    ]
    emit_main()

    summary = {
        "kind": "LocalControlNodeProcessSummary",
        "inputPath": str(input_path.resolve()),
        "bindingArtifact": str(binding_artifact.resolve()),
        "receiptArtifact": str((outdir / "local-control-node-receipt.json").resolve()),
        "result": "pass",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
