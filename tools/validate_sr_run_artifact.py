#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

METHODS = {"pysr", "sindy", "kan", "llm_sr", "tpsr"}
UNITS = {"consistent", "inconsistent", "unknown", "unchecked"}
PROMOTIONS = {"candidate", "proposed", "admitted", "rejected"}
HASH_FIELDS = [
    "datasetRef.uri",
    "datasetRef.contentHash",
    "methodFamily",
    "operatorLibrary.binaryOperators",
    "operatorLibrary.unaryOperators",
    "operatorLibrary.customOperators",
    "randomSeed",
    "runtimeEnvironment.packages",
    "candidateRefs[*].equationLatex",
]

class ValidationError(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("root must be object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_hex64(value: Any, field: str) -> None:
    require(isinstance(value, str), f"{field} must be string")
    require(len(value) == 64, f"{field} must be 64 chars")
    require(all(c in "0123456789abcdef" for c in value), f"{field} must be lowercase sha256 hex")


def validate_candidate(candidate: dict[str, Any]) -> None:
    for key in ["candidateId", "equationLatex", "nmse", "complexity", "unitsStatus", "promotionState"]:
        require(key in candidate, f"candidate missing {key}")
    require(isinstance(candidate["candidateId"], str) and candidate["candidateId"], "candidateId required")
    require(isinstance(candidate["equationLatex"], str) and candidate["equationLatex"], "equationLatex required")
    require(isinstance(candidate["nmse"], (int, float)) and candidate["nmse"] >= 0, "nmse must be nonnegative number")
    require(isinstance(candidate["complexity"], int) and candidate["complexity"] >= 1, "complexity must be positive integer")
    require(candidate["unitsStatus"] in UNITS, "invalid unitsStatus")
    require(candidate["promotionState"] in PROMOTIONS, "invalid promotionState")
    if candidate["unitsStatus"] == "inconsistent":
        require(candidate["promotionState"] in {"candidate", "rejected"}, "inconsistent units cannot be proposed or admitted")


def canonical_hash_payload(data: dict[str, Any]) -> bytes:
    payload = {
        "datasetRef": {
            "uri": data["datasetRef"]["uri"],
            "contentHash": data["datasetRef"]["contentHash"],
        },
        "methodFamily": data["methodFamily"],
        "operatorLibrary": {
            "binaryOperators": sorted(data["operatorLibrary"].get("binaryOperators", [])),
            "unaryOperators": sorted(data["operatorLibrary"].get("unaryOperators", [])),
            "customOperators": sorted(data["operatorLibrary"].get("customOperators", [])),
        },
        "randomSeed": data["randomSeed"],
        "runtimeEnvironment": {
            "packages": sorted(data["runtimeEnvironment"].get("packages", []), key=lambda p: (p.get("name", ""), p.get("version", "")))
        },
        "candidateRefs": sorted([c["equationLatex"] for c in data.get("candidateRefs", [])]),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def computed_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_hash_payload(data)).hexdigest()


def validate_run(data: dict[str, Any], check_hash: bool = True) -> None:
    required = ["runId", "datasetRef", "methodFamily", "operatorLibrary", "randomSeed", "runtimeEnvironment", "replayHash", "controlAuthority", "candidateRefs", "chronosCarrierId", "issuedAt"]
    for key in required:
        require(key in data, f"missing {key}")
    ds = data["datasetRef"]
    require(isinstance(ds, dict), "datasetRef must be object")
    require(isinstance(ds.get("uri"), str) and ds.get("uri"), "datasetRef.uri required")
    require_hex64(ds.get("contentHash"), "datasetRef.contentHash")
    require(ds.get("hashAlgorithm") == "sha256", "datasetRef.hashAlgorithm must be sha256")
    require(data["methodFamily"] in METHODS, "invalid methodFamily")
    ops = data["operatorLibrary"]
    require(isinstance(ops, dict), "operatorLibrary must be object")
    require(isinstance(ops.get("binaryOperators"), list), "binaryOperators must be array")
    require(isinstance(ops.get("unaryOperators"), list), "unaryOperators must be array")
    if "customOperators" in ops:
        require(isinstance(ops.get("customOperators"), list), "customOperators must be array")
    require(data["randomSeed"] is None or isinstance(data["randomSeed"], int), "randomSeed must be integer or null")
    env = data["runtimeEnvironment"]
    require(isinstance(env, dict), "runtimeEnvironment must be object")
    require(isinstance(env.get("packages"), list) and env["packages"], "runtimeEnvironment.packages required")
    for package in env["packages"]:
        require(isinstance(package, dict), "package must be object")
        require(isinstance(package.get("name"), str) and package.get("name"), "package.name required")
        require(isinstance(package.get("version"), str) and package.get("version"), "package.version required")
    rh = data["replayHash"]
    require(isinstance(rh, dict), "replayHash must be object")
    require_hex64(rh.get("value"), "replayHash.value")
    require(rh.get("algorithm") == "sha256", "replayHash.algorithm must be sha256")
    require(rh.get("coveredFields") == HASH_FIELDS, "replayHash.coveredFields mismatch")
    require(isinstance(data["controlAuthority"], bool), "controlAuthority must be boolean")
    if data["methodFamily"] == "sindy":
        require(data["controlAuthority"] is False, "sindy controlAuthority must be false")
    candidates = data["candidateRefs"]
    require(isinstance(candidates, list) and len(candidates) >= 1, "candidateRefs must be nonempty array")
    for candidate in candidates:
        require(isinstance(candidate, dict), "candidate ref must be object")
        validate_candidate(candidate)
    if check_hash:
        expected = data["replayHash"]["value"]
        actual = computed_hash(data)
        require(actual == expected, f"replayHash mismatch: computed {actual}, expected {expected}")


def validate_file(path: Path, check_hash: bool) -> tuple[bool, str | None]:
    try:
        data = load(path)
        validate_run(data, check_hash=check_hash)
        return True, None
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?")
    parser.add_argument("--fixtures")
    parser.add_argument("--expect-invalid", action="store_true")
    parser.add_argument("--skip-hash", action="store_true")
    args = parser.parse_args()
    paths: list[Path] = []
    if args.fixtures:
        root = Path(args.fixtures)
        paths.extend(sorted(root.glob("sr-run-artifact.valid.json")))
        paths.extend(sorted(root.glob("reject_*.json")))
        paths.extend(sorted(root.glob("reject-*.json")))
    elif args.fixture:
        paths = [Path(args.fixture)]
    else:
        parser.error("provide fixture or --fixtures")
    ok = True
    for path in paths:
        valid, error = validate_file(path, check_hash=not args.skip_hash)
        expected_invalid = args.expect_invalid or path.name.startswith("reject")
        accepted = (not valid) if expected_invalid else valid
        print(json.dumps({"path": str(path), "valid": valid, "expectedInvalid": expected_invalid, "error": error}, sort_keys=True))
        ok = ok and accepted
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
