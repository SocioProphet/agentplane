#!/usr/bin/env python3
"""Minimal tenant gateway dispatch stub for the first local-hybrid slice."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_dispatch(task: dict[str, Any], decision: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    if not decision.get("allow", False):
        raise ValueError("policy decision denies remote dispatch")
    transforms = decision.get("requiredTransformations", [])
    payload = {
        "taskId": task["taskId"],
        "capabilityInstanceId": binding["binding"]["capabilityInstanceId"],
        "workerEndpoint": binding["binding"]["workerEndpoint"],
        "executionLane": binding["binding"]["executionLane"],
        "requiredTransformations": transforms,
        "input": task["input"],
    }
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["dispatchDigest"] = "sha256:" + hashlib.sha256(payload_bytes).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", type=Path)
    parser.add_argument("decision", type=Path)
    parser.add_argument("binding", type=Path)
    args = parser.parse_args()
    dispatch = build_dispatch(load_json(args.task), load_json(args.decision), load_json(args.binding))
    print(json.dumps(dispatch, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
