#!/usr/bin/env python3
"""Deterministic replay/cairn materialization stub for the first local-hybrid slice."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def materialize(payload: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    task_id = payload["taskId"]
    journal_offset = payload["journalOffset"]
    artifact_id = f"artifact:{digest[:16]}"
    return {
        "cairnId": f"sha256:{digest}",
        "replayHandle": f"cairn://{task_id}/{journal_offset}",
        "artifacts": [
            {
                "artifactId": artifact_id,
                "digest": f"sha256:{hashlib.sha256((task_id + str(journal_offset)).encode('utf-8')).hexdigest()}"
            }
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    args = parser.parse_args()
    result = materialize(load_json(args.payload))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
