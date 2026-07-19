#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def uri_to_fixture_name(uri: str) -> str:
    return uri.rstrip("/").split("/")[-1] + ".json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal")
    parser.add_argument("--fixture-store", required=True)
    parser.add_argument("--expect-invalid", action="store_true")
    args = parser.parse_args()

    proposal = json.loads(Path(args.proposal).read_text(encoding="utf-8"))
    replay_ref = proposal.get("runArtifactRef")

    if not replay_ref:
        result = {"valid": False, "errorCode": "REPLAY_REF_MISSING"}
        print(json.dumps(result, sort_keys=True))
        return 0 if args.expect_invalid else 1

    artifact_path = Path(args.fixture_store) / uri_to_fixture_name(replay_ref)

    if not artifact_path.exists():
        result = {
            "valid": False,
            "errorCode": "REPLAY_REF_UNRESOLVABLE",
            "offendingUri": replay_ref,
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if args.expect_invalid else 1

    validator = Path(__file__).resolve().parent / "validate_replay_hash.py"
    completed = subprocess.run(
        [sys.executable, str(validator), str(artifact_path)],
        capture_output=True,
        text=True,
    )

    replay_valid = completed.returncode == 0

    if not replay_valid:
        result = {
            "valid": False,
            "errorCode": "REPLAY_HASH_MISMATCH",
            "artifact": str(artifact_path),
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if args.expect_invalid else 1

    result = {"valid": True, "artifact": str(artifact_path)}
    print(json.dumps(result, sort_keys=True))
    return 1 if args.expect_invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
