# Tensegrity Runtime Contract

## Purpose

AgentPlane's execution model is a **tensegrity structure**: agents, tools, services, models, repos, and hosts are **compression members** — structural elements that do work. They are stabilized by continuous **tension members**: policy, identity, provenance, tests, signatures, audits, ledgers, capability grants, replay, and revocation.

Neither class functions alone. A compression member without tension yields ungoverned execution. A tension member without a compression member yields policy theater with no work done.

This contract defines how AgentPlane enforces tensegrity at runtime.

## Compression Members

| Compression Member | Description |
|--------------------|-------------|
| Agent | Execution actor with bounded capability radius |
| Tool | Callable surface scoped by tool grant and CGRM decision |
| Service | External or internal service endpoint with policy gate |
| Model | Inference engine with model-routing lane decision |
| Repo | Source repository with branch and GitOps audit chain |
| Host | Execution environment with resource scope and capability radius R5 guard |

## Tension Members

| Tension Member | Description |
|----------------|-------------|
| Policy | Policy decision ref from PolicyFabric; required on every execution artifact |
| Identity | Actor ref and post/authority binding; required for all dispatches |
| Provenance | Hash-chain of inputs, prior artifacts, and upstream anchors |
| Tests | Validation receipts and verification execution receipts |
| Signatures | Attestation events and cryptographic seals on receipts |
| Audits | Audit trail refs on intervention outcomes and blocked dispatches |
| Ledgers | Evidence ledger refs and budget settlement receipts |
| Capability Grants | Tool grants scoped by CGRM and capability radius level |
| Replay | Replay artifact ref required on all governed runs |
| Revocation | Revocation path declared at compression member registration |

## Tensegrity Invariants

1. **No compression member executes without a policy tension member.** Every agent action, tool invocation, service call, and model routing decision must carry a `policy_decision_ref`.

2. **Tension members must form a closed chain.** Policy → Identity → Provenance → Evidence → Replay → Revocation must each reference the same run or be transitively linkable through `upstream_anchors`.

3. **Revocation dissolves a tension member's grip immediately.** A revoked capability grant, expired policy decision, or invalidated identity ref causes the dependent compression member to transition to `blocked` or `deferred` — not to `completed`.

4. **Replay seals the tensegrity loop.** A governed run without a `replay_artifact_ref` is structurally incomplete. Replay verifies that the compression-plus-tension envelope produces the same result under rerun, or surfaces a `divergence_record` for escalation.

5. **Oversteer detection is a governance obligation, not an optimization.** See `cybernetic-oversteer-v0.md`.

## Integration Points

- `ConversationalActionEvidence` — tension: policy, identity, replay_linkage
- `CivicStackRunCapsule` — tension: policy, provenance_refs, rationalgrl_trace, hellgraph_evidence_refs
- `BoundaryCalculusEvidenceEnvelope` — tension: promotion_gate, policy_result, attribution_discriminating_evidence_refs
- `GovernedRunContract` — tension: policy, budget, verifier chain, replay_artifact_ref
- `CapabilityRadiusProfile` — defines tension member scope per compression member level (R0–R5)
