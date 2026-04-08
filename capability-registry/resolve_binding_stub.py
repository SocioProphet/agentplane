#!/usr/bin/env python3
"""Minimal capability resolution stub for the first local-hybrid slice.

This script resolves a logical capability descriptor into a runtime binding.
It intentionally uses only the Python standard library so it can run in a bare
repository checkout.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_descriptor(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_binding(descriptor: dict[str, Any], requested_lane: str | None = None) -> dict[str, Any]:
    execution = descriptor.get("execution", {})
    binding = descriptor.get("binding", {})
    supported_lanes = execution.get("supportedLanes", [])
    lane = requested_lane or binding.get("executionLane") or execution.get("defaultLane")
    if lane not in supported_lanes:
        raise ValueError(f"unsupported lane: {lane!r}; supported={supported_lanes!r}")
    return {
        "resolved": True,
        "binding": {
            "capabilityInstanceId": binding["capabilityInstanceId"],
            "executionLane": lane,
            "workerEndpoint": binding["workerEndpoint"],
            "workerContract": binding["workerContract"],
            "credentialScope": binding["credentialScope"],
            "bindingTtlSeconds": binding["bindingTtlSeconds"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("descriptor", type=Path)
    parser.add_argument("--lane", default=None)
    args = parser.parse_args()
    descriptor = load_descriptor(args.descriptor)
    result = resolve_binding(descriptor, requested_lane=args.lane)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
