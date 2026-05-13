#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_NON_CLAIMS = {
    "no_runtime_replay_execution",
    "no_runtime_evidence_validation",
    "no_semantic_invariant_verification",
    "no_tag_promotion_decision",
    "no_runtime_circuit_discovery",
    "no_runtime_ablation_verification",
    "no_cross_plane_evidence_resolution",
    "no_cryptographic_authenticity_verification",
    "no_sourceos_spec_promotion",
}

FORBIDDEN_PHASE9_FIELDS = {
    "runtime_replay_execution",
    "runtime_evidence_validation",
    "semantic_invariant_verification",
    "tag_promotion_decision",
    "runtime_circuit_discovery",
    "runtime_ablation_verification",
    "cross_plane_evidence_resolution",
    "cryptographic_authenticity_verification",
    "sourceos_spec_promotion",
    "verified_tier2_mode",
    "semantic_correctness_proof",
    "empirical_measurement_verified",
}

CLASS_REQUIRED_FIELDS = {
    "lawful_learning_alignment_check": {
        "artifact_ref",
        "replay_seal",
        "invariants_checked",
        "overall_result",
    },
    "lawful_learning_circuit_admission": {
        "artifact_ref",
        "circuit_id",
        "discovery_evidence_ref",
        "ablation_evidence_ref",
        "replay_seal",
    },
    "lawful_learning_decision_emission": {
        "artifact_ref",
        "decision_id",
        "decision_type",
        "evidence_status_refs",
        "replay_seal",
    },
    "lawful_learning_replay_blackboxing": {
        "artifact_ref",
        "composed_seal",
        "seal_a_ref",
        "seal_b_ref",
        "composition_rule",
        "boundary_hash",
    },
}

CLASS_ARTIFACT_CLASS = {
    "lawful_learning_alignment_check": "AlignmentCheckArtifact",
    "lawful_learning_circuit_admission": "CircuitRegistryArtifact",
    "lawful_learning_decision_emission": "LawfulLearningDecisionArtifact",
    "lawful_learning_replay_blackboxing": "ReplayBlackBoxingArtifact",
}

HASH_FIELDS = {
    "replay_seal",
    "composed_seal",
    "seal_a_ref",
    "seal_b_ref",
    "boundary_hash",
    "discovery_evidence_ref",
    "ablation_evidence_ref",
}


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if not value.startswith("sha256:"):
        return False
    suffix = value[len("sha256:"):]
    return len(suffix) == 64 and all(ch in "0123456789abcdef" for ch in suffix)


def check_receipt(data: dict[str, Any]) -> tuple[bool, str]:
    required_top = {"schema_version", "receipt_id", "receipt_class", "source_repo", "artifact_ref", "non_claims"}
    missing_top = sorted(required_top - set(data))
    if missing_top:
        return False, f"missing required top-level fields: {missing_top}"

    if data.get("schema_version") != "1.0.0":
        return False, "schema_version must be 1.0.0"
    if data.get("source_repo") != "SocioProphet/superconscious":
        return False, "source_repo must be SocioProphet/superconscious"

    receipt_class = data.get("receipt_class")
    if receipt_class not in CLASS_REQUIRED_FIELDS:
        return False, f"unsupported receipt_class: {receipt_class}"

    forbidden_present = sorted(FORBIDDEN_PHASE9_FIELDS & set(data))
    if forbidden_present:
        return False, "Phase 9 receipt must not claim runtime/semantic verification; forbidden fields present: " + ", ".join(forbidden_present)

    non_claims = set(data.get("non_claims", []))
    if non_claims != REQUIRED_NON_CLAIMS:
        missing = sorted(REQUIRED_NON_CLAIMS - non_claims)
        extra = sorted(non_claims - REQUIRED_NON_CLAIMS)
        return False, f"non_claims must exactly match Phase 9 boundary; missing={missing} extra={extra}"

    class_missing = sorted(CLASS_REQUIRED_FIELDS[receipt_class] - set(data))
    if class_missing:
        return False, f"{receipt_class} missing required fields: {class_missing}"

    artifact_ref = data.get("artifact_ref")
    if not isinstance(artifact_ref, dict):
        return False, "artifact_ref must be object"
    expected_artifact_class = CLASS_ARTIFACT_CLASS[receipt_class]
    if artifact_ref.get("artifact_class") != expected_artifact_class:
        return False, f"artifact_ref.artifact_class must be {expected_artifact_class}"
    if not _is_sha256(artifact_ref.get("opaque_hash")):
        return False, "artifact_ref.opaque_hash must be sha256:<64 lowercase hex>"

    for field in HASH_FIELDS:
        if field in data and not _is_sha256(data[field]):
            return False, f"{field} must be sha256:<64 lowercase hex>"

    if "invariants_checked" in data:
        if not isinstance(data["invariants_checked"], list) or not data["invariants_checked"]:
            return False, "invariants_checked must be non-empty list"
    if "evidence_status_refs" in data:
        if not isinstance(data["evidence_status_refs"], list) or not data["evidence_status_refs"]:
            return False, "evidence_status_refs must be non-empty list"
    if "composition_rule" in data and not str(data.get("composition_rule", "")).strip():
        return False, "composition_rule must be non-empty"

    return True, "OK"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_lawful_learning_phase9_receipts.py <receipt.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    ok, message = check_receipt(data)
    if not ok:
        print(message, file=sys.stderr)
        return 1
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
