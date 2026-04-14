#!/usr/bin/env python3
"""Deterministic worker execution stub for the first local-hybrid slice."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_chunks(chunks: list[dict[str, Any]]) -> str:
    texts = [str(chunk.get("text", "")).strip() for chunk in chunks]
    joined = " ".join(part for part in texts if part)
    compact = " ".join(joined.split())
    return compact[:280]


def execute(request: dict[str, Any]) -> dict[str, Any]:
    chunks = request.get("input", {}).get("context", {}).get("chunks", [])
    summary = summarize_chunks(chunks)
    input_digest = "sha256:" + hashlib.sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output = {
        "summary": summary,
        "risks": [
            {"id": "r1", "text": "Replay semantics incomplete."},
            {"id": "r2", "text": "Tenant failover remains unspecified in the stub path."}
        ]
    }
    output_digest = "sha256:" + hashlib.sha256(
        json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "taskId": request["taskId"],
        "status": "completed",
        "output": output,
        "provenance": {
            "workerId": "worker:summarize-01",
            "modelId": "model:deterministic-stub-01",
            "toolchain": ["agentplane.worker-runtime.execute_stub"],
            "inputDigest": input_digest,
            "outputDigest": output_digest
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    result = execute(load_json(args.request))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
