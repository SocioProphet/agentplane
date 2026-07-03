# Content and Support Bundle Execution Design

## Purpose

This document defines how `agentplane` participates in governed content transformation, support remediation, premium-support actions, and query-driven execution handoff.

`agentplane` is the bounded execution plane. It does not decide semantic meaning or query policy. It executes validated bundles, emits evidence, and preserves replayability.

## Repository role

`agentplane` owns:

- bounded execution of transformation or remediation bundles
- evidence artifacts for validation, placement, run, replay, promotion, reversal, and session context
- execution-time enforcement of bundle policy constraints
- replayable execution receipts for support and content-change workflows

It does not own:

- ontology semantics (`ontogenesis`)
- transport/storage contract authority (`socioprophet-standards-storage`)
- query planning (`sherlock-search`)
- raw ops-domain normalization (`global-devsecops-intelligence`)
- long-horizon retained memory (`memory-mesh`)

## Supported execution categories

### Content transformation bundles

Used for:
- render or compose previews
- asset migration or restructuring
- re-index preparation
- promotion-ready packaging
- rollback / reversal preparation

### Support remediation bundles

Used for:
- bounded diagnostics
- guided remediation packaging
- escalation packet assembly
- premium-support overlay materialization
- runbook validation or generation workflows

### Query-triggered action bundles

Used when a query result includes a next-best-action that requires actual execution rather than plain retrieval.

Examples:
- validate affected assets before recommendation
- generate replayable support summary artifact
- create evidence bundle for anomaly-linked escalation
- run a bounded diagnostic against normalized incident context

## Required inputs

Execution should consume typed refs, not ad hoc strings.

At minimum:

- `BundleRef`
- `SupportInteractionRef`
- `QueryResultSetRef`
- `IncidentStoryRef`
- `AnomalyFindingRef`
- `PolicyBundleRef`
- `PremiumOverlayRef` when applicable
- `EvidenceRef` inputs

## Required outputs

Every execution path should preserve the evidence-forward posture.

At minimum:

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact`
- `ReplayArtifact`

And where applicable:

- `PromotionArtifact`
- `ReversalArtifact`
- `SessionArtifact`
- support-oriented evidence bundles or escalation attachments

## Support and premium-support implications

### Standard support

Standard support execution should remain tightly bounded:
- diagnostics
- evidence summarization
- limited remediation packaging
- no ungoverned cross-boundary publication

### Premium support

Premium support may execute richer bundles, but only with explicit overlay and entitlement context. Examples include:
- customer-specific runbook validation
- premium overlay materialization
- richer diagnostic bundles
- higher-grade escalation packet generation

### Mission-critical support

Mission-critical execution should require stronger human review, narrower bundle scopes, and stricter evidence obligations.

## Query handoff model

```text
Sherlock / Support Agent / Runtime API
  -> action suggestion selected
  -> policy and entitlement check
  -> bundle resolution
  -> agentplane validate / place / run
  -> evidence artifact generation
  -> replay handle emitted
  -> result returned to caller and retained in memory
```

## Integration map

- `sherlock-search`: upstream query and action-suggestion source
- `global-devsecops-intelligence`: normalized ops-domain findings used as execution context
- `memory-mesh`: retained execution history and writeback target
- `prophet-platform`: runtime host and evaluation lane around execution results
- `sociosphere`: workspace composition and deterministic materialization for execution lanes

## Immediate implementation tranche

1. Define support and content bundle categories and their typed refs.
2. Define evidence requirements for query-triggered and support-triggered executions.
3. Add replay expectations for support and premium-support bundle runs.
4. Align any future action-suggestion runtime with these execution categories.

## Outcome

When implemented correctly, `agentplane` becomes the governed execution plane for content, support, premium support, and query-triggered actions, while preserving replayability and evidence-forward operation.
