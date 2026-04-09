# Evidence-Native Assessment Runtime Binding v0

## Status

Plan document.

This document binds the evidence-native assessment contract pack into `agentplane` as the execution control plane.

## Canonical upstreams

- contracts and conformance: `SocioProphet/socioprophet-standards-storage`
- semantic context: `SocioProphet/socioprophet-standards-knowledge`
- policy source: `SocioProphet/policy-fabric`

`agentplane` remains the runtime consumer and receipt owner.

## Runtime role

`agentplane` does not author the control ontology. It executes pinned assessment bundles, preserves execution evidence, and seals replayable run records.

For the assessment slice, that means:
- accept a bundle or equivalent evaluator package derived from Policy Fabric
- run evidence-processing or control-evaluation steps on an approved executor
- preserve trace continuity across the run
- emit execution-plane evidence artifacts
- assemble or seal the final `AssessmentReceipt`

## First assessment bundle families

The first live slice should treat the following as distinct bundle families or stages:

1. evidence ingest / normalization
2. claim extraction
3. control evaluation
4. finding generation
5. reassessment / replay

These may run as one bundle in the smallest slice, but the contract boundaries should remain visible.

## Required runtime outputs

The assessment slice must preserve the existing execution evidence surfaces and add assessment-specific outputs.

### Existing execution evidence

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact`
- `ReplayArtifact`

### Assessment-specific outputs

- `ControlCellEvaluation` objects or a deterministic bundle containing them
- `Finding` objects or a deterministic bundle containing them
- sealed `AssessmentReceipt`

## Required invariants

1. Every `ControlCellEvaluation` emitted by the runtime must preserve:
   - `trace_id`
   - `row_id`
   - evaluator identity and version
   - policy bundle id and version
2. Every non-pass evaluation must include supporting evidence refs or explicit missing proof classes.
3. `AssessmentReceipt` sealing must fail closed when required fields are absent.
4. The runtime must not rescan upstream workspace state that was already emitted by the workspace controller; it should consume references.
5. Reassessment must preserve receipt lineage rather than overwrite prior evidence.

## Receipt mapping

The assessment slice should map onto the existing receipt lifecycle roughly as follows:

- workspace and context preparation come from upstream systems
- policy identity arrives from the policy bundle selected for the run
- placement is owned by `agentplane`
- run lifecycle is owned by `agentplane`
- assessment evaluation refs and finding refs are bound during or immediately after run completion
- `AssessmentReceipt` is sealed only after required evidence digests, evaluation refs, and replay material are present

## Monitor / policy / test lanes

The runtime-governance plan already identifies:
- policy gate
- monitor lane
- generated test lane

The assessment slice should bind to those same surfaces.

### Policy gate

Use row-derived decision logic to drive allow / warn / deny / require-approval behavior.

### Monitor lane

Generate stale-review, drift, or evidence-age checks tied to row ids and receipt lineage.

### Test lane

Generate high-risk control checks that can be run in integration or release paths.

## Non-goals for v0

This binding does not require `agentplane` to:
- own stakeholder reporting UX
- become a document management system
- become the canonical home of framework ontology
- replace Policy Fabric or the standards repos

## Acceptance gate

The runtime binding is acceptable for v0 when one complete governed run can produce:
- execution evidence artifacts
- at least one `ControlCellEvaluation`
- at least one `Finding`
- one sealed `AssessmentReceipt`
- one successful replay path with stable lineage
