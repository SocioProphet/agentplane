#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_NON_CLAIMS = {
    "no_runtime_receipt_lookup",
    "no_runtime_non_claim_verification",
    "no_runtime_monitor_attestation",
    "no_timestamp_authenticity",
    "opaque_hashes_not_resolved",
    "no_runtime_replay_execution",
    "no_runtime_evidence_validation",
    "no_runtime_execution_attestation",
    "no_bundle_to_run_integrity_check",
    "no_cross_plane_evidence_resolution",
}

FORBIDDEN_RUNTIME_OR_FULL_COMPOSITION_FIELDS = {
    "receipt_integration",
    "authority_scope_analysis",
    "non_claim_analysis",
    "monitor_independence_analysis",
    "evidence_freshness_analysis",
    "evidence_receipt_refs_resolved",
    "resolved_receipts",
    "runtime_receipt_lookup",
    "runtime_replay_execution",
    "runtime_evidence_validation",
    "runtime_execution_attestation",
    "bundle_to_run_integrity_check",
    "cross_plane_evidence_resolution",
    "executed_replay_bundle",
    "validated_evidence_content",
    "execution_attestation",
    "bundle_run_integrity_result",
    "resolved_cross_plane_refs",
    "execution_status",
    "ledger_entry",
    "timestamp_authenticity_proof",
    "monitor_attestation_token",
}

MULTI_REF_FIELDS = (
    "evidence_receipt_refs",
    "replay_bundle_refs",
    "execution_run_refs",
    "validation_evidence_refs",
    "agentplane_run_ledger_refs",
)


def _check_hash_ref(ref: dict, label: str) -> tuple[bool, str]:
    opaque_hash = ref.get("opaque_hash", "")
    if not opaque_hash.startswith("sha256:"):
        return False, f"{label}.opaque_hash must use sha256: prefix"
    return True, ""


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_agentplane_evidence_receipt_composition_tier2_binding.py <fixture.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))

    non_claims = set(data.get("non_claims", []))
    if non_claims != REQUIRED_NON_CLAIMS:
        missing = sorted(REQUIRED_NON_CLAIMS - non_claims)
        extra = sorted(non_claims - REQUIRED_NON_CLAIMS)
        print(
            f"non_claims must exactly match required AgentPlane doctrine boundary; missing={missing} extra={extra}",
            file=sys.stderr,
        )
        return 1

    forbidden_present = sorted(FORBIDDEN_RUNTIME_OR_FULL_COMPOSITION_FIELDS & set(data))
    if forbidden_present:
        print(
            "AgentPlane evidence receipt Tier 2 binding must remain doctrine-only; forbidden fields present: "
            + ", ".join(forbidden_present),
            file=sys.stderr,
        )
        return 1

    for field in MULTI_REF_FIELDS:
        for idx, ref in enumerate(data.get(field, [])):
            ok, message = _check_hash_ref(ref, f"{field}[{idx}]")
            if not ok:
                print(message, file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
