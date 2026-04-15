# Context vs Human-Governance Boundary

This note clarifies a boundary that must remain explicit in the local-hybrid and receipt-integrated architecture.

## Separation rule

Two adjacent planes participate in governed execution, but they are not the same surface and should not be collapsed together.

### 1. Governed context plane
**Repository:** `slash-topics`

Owns:
- topic-pack identity
- pack digests
- locality class
- provenance references
- cache hit/miss facts
- remote fetch counts
- context-surface metadata used to reason about working-set quality and movement cost

### 2. Human-governance plane
**Repository:** `human-digital-twin`

Owns:
- policy bundle identity
- consent state
- approval requirement
- approval outcome
- attestation references
- human-facing trust-membrane semantics
- evidence needed to justify or replay human-governed decisions

## Why this matters in `agentplane`

`agentplane` assembles receipts and coordinates execution, so it sees both planes at once.
That does **not** make it the owner of either plane's semantics.

The correct relationship is:
- `slash-topics` contributes context facts to the receipt
- `human-digital-twin` contributes human-governance facts to the receipt
- `agentplane` joins them at execution and receipt boundaries without muddying the ownership split

## Practical effect

When extending the local-hybrid slice or the receipt lifecycle:
- do not push topic-pack identity/provenance work into HDT
- do not push approval/consent/attestation work into topic-surface docs
- keep event schemas and fixtures separate until they meet at receipt assembly

## Related docs

- `docs/local_hybrid_slice_v0.md`
- `docs/receipt-lifecycle.md`
- `docs/instrumentation/live_receipt_integration_plan.md`
