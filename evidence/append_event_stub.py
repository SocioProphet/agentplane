#!/usr/bin/env python3
"""Deterministic evidence append stub for the first local-hybrid slice."""

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


def append_event(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload.get("event", payload)
    digest = hashlib.sha256(canonical_bytes(event)).hexdigest()
    journal_offset = int(digest[:12], 16)
    return {
        "appended": True,
        "journalOffset": journal_offset,
        "evidenceDigest": f"sha256:{digest}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    args = parser.parse_args()
    result = append_event(load_json(args.payload))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
