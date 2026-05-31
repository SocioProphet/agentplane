#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

MODES = {"equation_discovery", "model_compression", "curriculum", "platform_dynamics", "program_search"}
METHODS = {"pysr", "sindy", "kan", "llm_sr", "tpsr"}
STATES = {"ineligible", "review_required", "eligible"}
OPTIONAL = {"nonAuthorityDeclaration", "notes"}
REQUIRED = {
    "policyId",
    "schemaVersion",
    "applicationMode",
    "methodFamilies",
    "minimumDatasetRows",
    "maximumCandidateComplexity",
    "maximumNmse",
    "requiredUnitsStatus",
    "requireReplayVerified",
    "allowControlAuthority",
    "forbiddenGovernanceFlags",
    "promotionEligibility",
}


class ValidationError(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    check(isinstance(data, dict), "root must be object")
    return data


def validate(data: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(data))
    extra = sorted(set(data) - REQUIRED - OPTIONAL)
    check(not missing, f"missing fields: {missing}")
    check(not extra, f"unexpected fields: {extra}")
    check(isinstance(data["policyId"], str) and data["policyId"].startswith("urn:"), "policyId must be URN")
    check(data["schemaVersion"] == "0.1.0", "schemaVersion mismatch")
    check(data["applicationMode"] in MODES, "invalid applicationMode")

    methods = data["methodFamilies"]
    check(isinstance(methods, list) and methods, "methodFamilies must be non-empty list")
    check(len(methods) == len(set(methods)), "methodFamilies must be unique")
    check(all(method in METHODS for method in methods), "invalid method family")

    check(isinstance(data["minimumDatasetRows"], int) and data["minimumDatasetRows"] >= 1, "minimumDatasetRows must be positive")
    check(isinstance(data["maximumCandidateComplexity"], int) and data["maximumCandidateComplexity"] >= 1, "maximumCandidateComplexity must be positive")
    check(isinstance(data["maximumNmse"], (int, float)) and data["maximumNmse"] >= 0, "maximumNmse must be nonnegative")
    check(data["requiredUnitsStatus"] == "consistent", "requiredUnitsStatus must be consistent")
    check(data["requireReplayVerified"] is True, "requireReplayVerified must be true")
    check(data["allowControlAuthority"] is False, "allowControlAuthority must be false")
    check(isinstance(data["forbiddenGovernanceFlags"], list), "forbiddenGovernanceFlags must be list")
    check(all(isinstance(flag, str) and flag for flag in data["forbiddenGovernanceFlags"]), "governance flag entries must be strings")
    check(data["promotionEligibility"] in STATES, "invalid promotionEligibility")
    if data["applicationMode"] == "platform_dynamics":
        check(data["promotionEligibility"] != "eligible", "platform_dynamics requires review boundary")


def validate_path(path: Path) -> tuple[bool, str | None]:
    try:
        validate(load_json(path))
        return True, None
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?")
    parser.add_argument("--fixtures")
    parser.add_argument("--expect-invalid", action="store_true")
    args = parser.parse_args()

    if args.fixtures:
        root = Path(args.fixtures)
        paths = sorted(root.glob("sr-gate-policy.valid.json"))
        paths.extend(sorted(root.glob("reject-sr-gate-policy-*.json")))
    elif args.fixture:
        paths = [Path(args.fixture)]
    else:
        parser.error("provide fixture or --fixtures")

    ok = True
    for path in paths:
        valid, error = validate_path(path)
        expected_invalid = args.expect_invalid or path.name.startswith("reject")
        accepted = (not valid) if expected_invalid else valid
        print(json.dumps({"path": str(path), "valid": valid, "expectedInvalid": expected_invalid, "error": error}, sort_keys=True))
        ok = ok and accepted
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
