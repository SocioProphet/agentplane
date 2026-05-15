#!/usr/bin/env python3
"""Deterministic structural validation for action proposal/admission/receipt contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "fixtures" / "action-contracts"

ACTION_PROPOSAL_SCHEMA = SCHEMAS / "action-proposal.schema.v0.1.json"
ACTION_ADMISSION_SCHEMA = SCHEMAS / "action-admission.schema.v0.1.json"
RUNTIME_RECEIPT_SCHEMA = SCHEMAS / "runtime-receipt.schema.v0.1.json"

GAIA_PROPOSAL = FIXTURES / "gaia-tile-manifest.proposal.v0.1.json"
GAIA_ADMISSION = FIXTURES / "gaia-tile-manifest.admission.v0.1.json"
GAIA_RECEIPT = FIXTURES / "gaia-tile-manifest.runtime-receipt.v0.1.json"
ARTIFACT_PROPOSAL = FIXTURES / "artifact-review.proposal.v0.1.json"
ARTIFACT_ADMITTED = FIXTURES / "artifact-review.admission-admitted.v0.1.json"
ARTIFACT_DENIED = FIXTURES / "artifact-review.admission-denied.v0.1.json"


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected object in {path.relative_to(ROOT)}")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_schema_headers() -> None:
    for path, title in (
        (ACTION_PROPOSAL_SCHEMA, "ActionProposal"),
        (ACTION_ADMISSION_SCHEMA, "ActionAdmission"),
        (RUNTIME_RECEIPT_SCHEMA, "RuntimeReceipt"),
    ):
        schema = load(path)
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{path.name} draft mismatch")
        require(schema.get("title") == title, f"{path.name} title mismatch")


def validate_gaia_flow() -> None:
    proposal = load(GAIA_PROPOSAL)
    admission = load(GAIA_ADMISSION)
    receipt = load(GAIA_RECEIPT)

    require(proposal.get("kind") == "ActionProposal", "gaia proposal kind mismatch")
    require(admission.get("kind") == "ActionAdmission", "gaia admission kind mismatch")
    require(receipt.get("kind") == "RuntimeReceipt", "gaia receipt kind mismatch")

    require(admission.get("proposalRef") == proposal.get("proposalId"), "gaia admission must reference proposal")
    require(receipt.get("proposalRef") == proposal.get("proposalId"), "gaia receipt must reference proposal")
    require(receipt.get("admissionRef") == admission.get("admissionId"), "gaia receipt must reference admission")

    similarity = proposal.get("priorActionSimilarity", {})
    vector_candidates = similarity.get("vectorCandidates", [])
    require(similarity.get("reEvaluationRequired") is True, "gaia vector similarity must require re-evaluation")
    require(len(vector_candidates) >= 1, "gaia vector similarity candidate missing")
    for candidate in vector_candidates:
        require(candidate.get("candidateOnly") is True, "vector candidate must be candidate_only")
        require(candidate.get("admissionAuthority") is False, "vector candidate cannot authorize admission")

    require(admission.get("status") == "admitted", "gaia admission should be admitted")
    require(admission.get("runtimeBoundary"), "gaia admission must include runtimeBoundary")

    required_receipt_fields = {
        "agentIdentity",
        "runtimeIdentity",
        "runtimeProfile",
        "inputHash",
        "outputHash",
        "logsRef",
        "policyDecisionRef",
        "startTime",
        "endTime",
        "status",
    }
    missing = sorted(field for field in required_receipt_fields if field not in receipt)
    require(not missing, f"gaia runtime receipt missing required fields: {', '.join(missing)}")


def validate_artifact_review_records() -> None:
    proposal = load(ARTIFACT_PROPOSAL)
    admitted = load(ARTIFACT_ADMITTED)
    denied = load(ARTIFACT_DENIED)

    require(proposal.get("kind") == "ActionProposal", "artifact review proposal kind mismatch")
    require(admitted.get("status") == "admitted", "artifact review admitted record status mismatch")
    require(denied.get("status") == "denied", "artifact review denied record status mismatch")
    require(admitted.get("proposalRef") == proposal.get("proposalId"), "admitted record must reference artifact review proposal")
    require(denied.get("proposalRef") == proposal.get("proposalId"), "denied record must reference artifact review proposal")
    require(bool(denied.get("reason")), "denied record must include reason")


def main() -> int:
    validate_schema_headers()
    validate_gaia_flow()
    validate_artifact_review_records()
    print("OK: validated action proposal/admission/runtime receipt contracts and fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
