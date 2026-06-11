# IOES Execution Evidence Integration

Status: draft integration contract

## Purpose

This note defines the AgentPlane evidence slice for IOES: Identity, Ontogenesis, Ecology, and Stewardship.

AgentPlane does not decide human identity, own stewardship relationships, promote curriculum canon, or convert delivery metrics into human value. Its role is narrower and stricter: validate execution posture, run or route approved bundles, emit replayable evidence, and preserve repair/reversal context.

In small words: AgentPlane is the receipt machine, not the philosopher king. Tiny crown revoked.

## IOES-impacting execution

An execution is IOES-impacting when a bundle observes, infers, proposes, mutates, exports, remembers, repairs, or routes any of the following:

- identity continuity or projection state
- consent state
- ontogenesis/developmental state
- stewardship assignment or transfer
- keeper logs
- succession rules
- abandonment signals
- Gaia/ecological dependency records
- learning artifact promotion
- next-best-action learning output
- delivery outcome scoring
- human digital twin continuity claims
- HolographMe/persona projection records

IOES-impacting bundles must fail closed unless policy, authority, evidence, and replay posture are explicit.

## Required evidence references

An IOES execution receipt should include:

- `bundle_ref`
- `policy_decision_ref`
- `authority_ref`
- `consent_ref`, when projection, export, mutation, or human-impacting memory is involved
- `input_evidence_refs`
- `validation_artifact_ref`
- `placement_decision_ref`
- `run_artifact_ref`
- `replay_artifact_ref`
- `repair_or_reversal_ref`, where available
- `procybernetica_conformance_ref`
- `policy_fabric_veto_profile_ref`
- `regis_graph_delta_ref`
- `delivery_outcome_ref`, when delivery metrics are emitted
- `learning_artifact_ref`, when curriculum or canon state is touched

## Receipt shape

A minimal IOES execution receipt has this conceptual shape:

```json
{
  "receipt_type": "IOESExecutionEvidence",
  "schema_version": "0.1",
  "receipt_id": "ioes_exec_...",
  "bundle_ref": "bundle:...",
  "execution_status": "accepted|denied|repaired|reversed|review_required",
  "ioes_impact_classes": ["learning_canon", "stewardship_assignment"],
  "policy_decision_ref": "policy-fabric:...",
  "authority_refs": ["authority:..."],
  "consent_refs": ["consent:..."],
  "input_evidence_refs": ["evidence:..."],
  "validation_artifact_ref": "agentplane:validation:...",
  "placement_decision_ref": "agentplane:placement:...",
  "run_artifact_ref": "agentplane:run:...",
  "replay_artifact_ref": "agentplane:replay:...",
  "repair_or_reversal_ref": "agentplane:repair:...",
  "external_refs": {
    "procybernetica_conformance_ref": "procybernetica:...",
    "policy_fabric_veto_profile_ref": "policy-fabric:...",
    "regis_graph_delta_ref": "regis:...",
    "delivery_outcome_ref": "delivery:...",
    "learning_artifact_ref": "alexandrian:..."
  },
  "non_claims": [
    "This receipt is not human consent.",
    "This receipt is not canon promotion by itself.",
    "This receipt is not a human-worth score."
  ]
}
```

## Admission invariants

AgentPlane should reject or route to review when:

1. An IOES-impacting bundle lacks a Policy Fabric decision.
2. A human-impacting mutation lacks authority.
3. Projection or export lacks consent evidence.
4. Learning canon promotion lacks stewardship and succession evidence.
5. Delivery scoring lacks non-claim boundaries against human-worth or productivity-score interpretation.
6. Any human-impacting execution is not replayable or lacks a repair/reversal path.
7. The bundle attempts to treat a twin, projection, score, role, credential, or agent summary as the person.

## Non-claims

This integration does not make AgentPlane the policy authority.

This integration does not make AgentPlane the source of identity truth.

This integration does not allow agent execution to substitute for human consent.

This integration does not certify an IOES action as morally sufficient. It only supplies the validation, execution, replay, and repair evidence needed by the broader governance stack.

## Cross-stack alignment

- ProCybernetica defines the doctrine and conformance posture.
- Policy Fabric defines protected-value veto logic.
- Regis materializes graph memory for stewardship, succession, ontogenesis, and Gaia dependency.
- Alexandrian Academy owns learning artifact stewardship and canon promotion records.
- Delivery Excellence owns outcome records that explicitly reject productivity-only human scoring.
- AgentPlane emits execution evidence and replay/repair receipts.

The invariant is simple: no receipt, no promotion. No consent, no projection. No keeper/succession, no canon. No repair path, no human-impacting mutation.
