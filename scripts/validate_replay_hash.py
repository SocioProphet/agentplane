#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def canonicalize_packages(packages):
    return sorted(packages, key=lambda p: (p.get("name", ""), p.get("version", "")))


def canonicalize_operators(ops):
    return sorted(ops or [])


def build_hash_payload(data):
    payload = {
        "datasetRef": {
            "uri": data["datasetRef"]["uri"],
            "contentHash": data["datasetRef"]["contentHash"],
        },
        "methodFamily": data["methodFamily"],
        "operatorLibrary": {
            "binaryOperators": canonicalize_operators(data["operatorLibrary"].get("binaryOperators", [])),
            "unaryOperators": canonicalize_operators(data["operatorLibrary"].get("unaryOperators", [])),
            "customOperators": canonicalize_operators(data["operatorLibrary"].get("customOperators", [])),
        },
        "randomSeed": data["randomSeed"],
        "runtimeEnvironment": {
            "packages": canonicalize_packages(data["runtimeEnvironment"].get("packages", []))
        },
        "candidateRefs": sorted(
            [c["equationLatex"] for c in data.get("candidateRefs", [])]
        ),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def validate(path: Path) -> tuple[bool, str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = build_hash_payload(data)
    computed = hashlib.sha256(payload).hexdigest()
    expected = data["replayHash"]["value"]
    return computed == expected, computed, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    parser.add_argument("--expect-invalid", action="store_true")
    args = parser.parse_args()

    valid, computed, expected = validate(Path(args.artifact))

    result = {
        "valid": valid,
        "computedHash": computed,
        "expectedHash": expected,
    }
    print(json.dumps(result, sort_keys=True))

    if args.expect_invalid:
        return 0 if not valid else 1
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
