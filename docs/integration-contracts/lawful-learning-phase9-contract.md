# Lawful-learning Phase 9 AgentPlane Integration Contract

**Status:** v1 doctrine/spec contract.

**Date:** May 13, 2026

**Scope:** Defines the runtime-evidence integration boundary between `SocioProphet/superconscious` lawful-learning artifacts and `SocioProphet/agentplane` evidence receipts.

**Boundary:** This document is doctrine/specification only. It defines receipt classes and structural validation expectations. It does not add runtime replay execution, semantic verification of lawful-learning invariant outcomes, cross-plane evidence dereferencing, or cryptographic authenticity verification.

## 1. Upstream producer

The upstream producer is:

```text
SocioProphet/superconscious
```

The relevant upstream surfaces are:

```text
docs/lawful-learning/
schemas/lawful-learning/
scripts/check-lawful-learning.py
tests/fixtures/lawful-learning/
examples/TRUST_SURFACE.lawful-learning.yaml
```

The Phase 8 estate registration in `SocioProphet/sociosphere` records AgentPlane as the future runtime evidence owner for lawful-learning.

## 2. AgentPlane intake artifacts

AgentPlane recognizes four lawful-learning artifact classes at Phase 9.

### 2.1 AlignmentCheckArtifact

An `AlignmentCheckArtifact` is the output of `check-lawful-learning.py` over a lawful-learning target such as a training run, composition declaration, circuit registry entry, or trust-surface artifact.

AgentPlane receives:

```text
artifact_ref
replay_seal
invariants_checked
overall_result
non_claims
```

AgentPlane validates only the structure of the receipt. It does not decide whether the invariant outcome was substantively correct.

### 2.2 CircuitRegistryArtifact

A `CircuitRegistryArtifact` records an admitted or candidate circuit registry entry from the lawful-learning lane.

AgentPlane receives:

```text
circuit_id
discovery_evidence_ref
ablation_evidence_ref
replay_seal
non_claims
```

AgentPlane validates that the receipt has the required references. It does not run circuit discovery or ablation studies.

### 2.3 LawfulLearningDecisionArtifact

A `LawfulLearningDecisionArtifact` records a lawful-learning decision emission event.

AgentPlane receives:

```text
decision_id
decision_type
evidence_status_refs
replay_seal
non_claims
```

AgentPlane validates that the decision is evidence-bound and replay-sealed. It does not evaluate whether the decision was correct.

### 2.4 ReplayBlackBoxingArtifact

A `ReplayBlackBoxingArtifact` records the structural replay-seal relationship specified by `replay_seal_for_composed_trace`.

AgentPlane receives:

```text
composed_seal
seal_a_ref
seal_b_ref
composition_rule
boundary_hash
non_claims
```

At Phase 9, AgentPlane validates the declared fields and the doctrine boundary. It does not execute constituent adapters and does not claim cryptographic authenticity of the seals.

## 3. What AgentPlane validates at Phase 9

AgentPlane validates the following structural properties:

```text
receipt_class is one of the four lawful-learning classes
required fields are present for the receipt class
replay_seal or composed_seal is present where required
non_claims preserve the Phase 9 boundary
receipts do not claim semantic verification
receipts do not claim runtime replay execution
receipts do not claim cross-plane evidence resolution
```

## 4. What AgentPlane does not validate at Phase 9

AgentPlane does not validate:

```text
substantive correctness of invariant outcomes
substantive correctness of claim promotion decisions
runtime circuit discovery
runtime ablation verification
cryptographic authenticity of replay seals
empirical_measurement_ref existence or accuracy
cross-plane evidence resolution
transitive supersession-chain traversal
Tier 2 verified modes
```

These remain deferred.

## 5. Receipt class schema

The receipt classes are specified in:

```text
schemas/receipts/lawful-learning-receipt-classes.v1.json
```

The schema is repo-local to AgentPlane at Phase 9. It is not promoted to a shared standard in this PR.

## 6. Fixture discipline

Phase 9 includes:

```text
positive fixture per receipt class
negative fixture: missing replay seal
negative fixture: semantic verification claim
```

The negative fixtures are the load-bearing enforcement surface. They prevent a future refactor from treating Phase 9 receipts as semantic verification or runtime execution receipts.

## 7. Non-claims

The Phase 9 contract itself carries these non-claims:

```text
no_runtime_replay_execution
no_runtime_evidence_validation
no_semantic_invariant_verification
no_tag_promotion_decision
no_runtime_circuit_discovery
no_runtime_ablation_verification
no_cross_plane_evidence_resolution
no_cryptographic_authenticity_verification
no_sourceos_spec_promotion
```

## 8. Future work

Future work may introduce:

```text
verified replay execution receipts
cryptographic timestamp/authenticity proofs
cross-plane evidence resolvers
empirical measurement resolvers
Tier 2 verified modes
sourceos-spec promotion of stable receipt schemas
```

Those are explicitly outside Phase 9 v1.
