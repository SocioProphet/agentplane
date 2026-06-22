# Boundary Calculus Evidence Envelope Integration

AgentPlane emits a `BoundaryCalculusEvidenceEnvelope` when an agent uses the Boundary Calculus claim discipline. SocioSphere owns the standard and the promotion/demotion controller.

## Boundary

- AgentPlane: emits evidence envelopes, enforces policy gates, provides replay artifacts.
- SocioSphere: owns the Boundary Calculus standard, controls claim promotion/demotion.
- AgentPlane does not promote or demote claims unilaterally.

## Envelope fields

| Field | Required | Description |
|-------|----------|-------------|
| `claim_id` | Yes | Stable identifier for this claim instance |
| `claim_status` | Yes | `observation` / `hypothesis` / `supported` / `confirmed` / `falsified` / `metaphor` / `load_bearing_assertion` |
| `local_model` | Yes | Model or agent producing the claim |
| `boundary_or_interface` | Yes | The boundary or interface at which the claim is evaluated |
| `load_bearing` | No | Whether the claim is load-bearing in a downstream decision or security gate |
| `non_claims` | Yes | Explicit list of what this envelope does NOT assert (minItems 1) |
| `evidence_refs` | Yes | References to supporting evidence (minItems 1) |
| `promotion_gate` | Yes | Gate required before promotion: `none_required` / `peer_review` / `sociosphere_controller` / `policy_fabric_evaluation` / `agentplane_replay_verification` |
| `policy_result` | Yes | `allow` / `allow_with_warning` / `block` / `escalate` / `pending_review` |
| `security_escalation_ref` | Conditional | Required when `policy_result=escalate` |
| `attribution_source` | No | Attribution claim source; if present, requires `attribution_discriminating_evidence_refs` |

## Policy hooks

The validator warns or blocks when:

- `claim_status=metaphor` and `load_bearing=true` — metaphors must not be load-bearing.
- `claim_status` is `confirmed` or `load_bearing_assertion` and `promotion_gate=none_required` — strong claims require a gate.
- `policy_result=escalate` without a `security_escalation_ref` — security escalations must reference their escalation record.
- `attribution_source` is present without `attribution_discriminating_evidence_refs` — attribution without discriminating evidence is not valid.

## Schema location

`schemas/boundary-calculus-evidence-envelope.schema.v0.1.json`

## Validation

```
make validate-boundary-calculus-evidence
```

## Example: supported claim

```json
{
  "kind": "BoundaryCalculusEvidenceEnvelope",
  "claim_status": "supported",
  "promotion_gate": "peer_review",
  "policy_result": "allow",
  "non_claims": ["This envelope does not authorize deployment."],
  "evidence_refs": ["evidence://agentplane/run/.../policy-gate-trace"]
}
```

## Example: security escalation

When a hypothesis at a security boundary triggers escalation:

```json
{
  "claim_status": "hypothesis",
  "load_bearing": true,
  "promotion_gate": "policy_fabric_evaluation",
  "policy_result": "escalate",
  "security_escalation_ref": "escalation://security/agentplane/..."
}
```

## Non-claims

This document does not:
- Define the Boundary Calculus standard (SocioSphere owns this).
- Grant AgentPlane authority to promote or demote claims.
- Certify that claim evidence is complete or sufficient for downstream use.
