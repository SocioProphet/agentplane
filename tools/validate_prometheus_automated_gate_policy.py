#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_POLICY_FIELDS = {
    "policyId",
    "policyVersion",
    "minimumDatasetSize",
    "nmseCeiling",
    "complexityCeiling",
    "requiredUnitsStatus",
    "replayHashVerificationRequired",
    "maxChronosGovernanceFlags",
    "eligibleReviewSurface",
    "decisionBoundary",
    "finalAdmissionAllowed",
    "issuedAt",
}
REQUIRED_EVALUATION_FIELDS = {
    "evaluationId",
    "policyId",
    "candidateId",
    "datasetSize",
    "nmse",
    "complexity",
    "unitsStatus",
    "replayHashVerified",
    "chronosGovernanceFlags",
    "requestedReviewSurface",
    "finalAdmissionRequested",
    "issuedAt",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"expected object: {path}")
    return data


def require_fields(data: dict[str, Any], fields: set[str], label: str) -> None:
    missing = fields - set(data)
    if missing:
        fail(f"{label} missing fields: {sorted(missing)}")


def validate_policy(policy: dict[str, Any]) -> None:
    require_fields(policy, REQUIRED_POLICY_FIELDS, "policy")
    if policy["minimumDatasetSize"] < 1:
        fail("policy minimumDatasetSize must be positive")
    if policy["nmseCeiling"] < 0:
        fail("policy nmseCeiling must be non-negative")
    if policy["complexityCeiling"] < 1:
        fail("policy complexityCeiling must be positive")
    if policy["requiredUnitsStatus"] != "consistent":
        fail("policy requiredUnitsStatus must be consistent")
    if policy["replayHashVerificationRequired"] is not True:
        fail("policy must require replay hash verification")
    if policy["maxChronosGovernanceFlags"] != 0:
        fail("policy maxChronosGovernanceFlags must be zero")
    if policy["eligibleReviewSurface"] != "automated_shacl_gate":
        fail("policy review surface must be automated_shacl_gate")
    if policy["decisionBoundary"] != "eligibility_only":
        fail("policy decision boundary must be eligibility_only")
    if policy["finalAdmissionAllowed"] is not False:
        fail("policy must not allow final admission")


def validate_evaluation(policy: dict[str, Any], evaluation: dict[str, Any]) -> None:
    require_fields(evaluation, REQUIRED_EVALUATION_FIELDS, "evaluation")
    if evaluation["policyId"] != policy["policyId"]:
        fail("evaluation policyId mismatch")
    if evaluation["datasetSize"] < policy["minimumDatasetSize"]:
        fail("datasetSize below policy threshold")
    if evaluation["nmse"] > policy["nmseCeiling"]:
        fail("nmse above policy threshold")
    if evaluation["complexity"] > policy["complexityCeiling"]:
        fail("complexity above policy threshold")
    if evaluation["unitsStatus"] != policy["requiredUnitsStatus"]:
        fail("unitsStatus does not meet policy")
    if policy["replayHashVerificationRequired"] and evaluation["replayHashVerified"] is not True:
        fail("replay hash verification required")
    if len(evaluation["chronosGovernanceFlags"]) > policy["maxChronosGovernanceFlags"]:
        fail("CHRONOS governance flags force human review")
    if evaluation["requestedReviewSurface"] != policy["eligibleReviewSurface"]:
        fail("requested review surface is not automated gate")
    if evaluation["finalAdmissionRequested"] is True:
        fail("automated gate cannot request final admission")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    parser.add_argument("--evaluation", required=True)
    parser.add_argument("--expect-invalid", action="store_true")
    args = parser.parse_args()

    policy_path = Path(args.policy)
    evaluation_path = Path(args.evaluation)
    try:
        policy = load(policy_path)
        evaluation = load(evaluation_path)
        validate_policy(policy)
        validate_evaluation(policy, evaluation)
        valid = True
        error = None
    except SystemExit as exc:
        valid = False
        error = str(exc)
    result = {"valid": valid, "evaluation": str(evaluation_path), "error": error}
    print(json.dumps(result, sort_keys=True))
    if args.expect_invalid:
        return 0 if not valid else 1
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
