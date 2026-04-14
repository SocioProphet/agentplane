# Intell-agency verdict consumption v0

## Status

Plan/spec document.

This document defines the first expected runtime-governance seam between Policy Fabric intell-agency verdict outputs and Agentplane execution eligibility.

## Upstream assumption

The governing policy and verdict semantics live upstream in `SocioProphet/policy-fabric`.

Agentplane is the execution-plane consumer.

## Initial enforcement surface

Before governed execution proceeds, Agentplane should consume a verdict envelope that identifies:

- governing policy bundle id and version
- target domain or execution lane
- rights-critical classification
- promote / block result
- failed predicates when blocked
- references to verdict and explanation artifacts

## Execution decision rule

The initial decision rule is intentionally narrow:

1. if the lane is governed and verdict material is missing, fail closed
2. if the verdict says `promote = false`, fail closed
3. if the verdict says `promote = true`, continue into bundle validation / placement / run
4. preserve governing references in downstream evidence artifacts

## Evidence expectations

The downstream execution evidence should preserve enough material to answer:

- which upstream policy bundle governed the decision?
- which verdict artifact authorized or blocked execution?
- which predicates failed when execution was blocked?
- which replay/evidence artifacts correspond to that blocked or allowed decision?

## Minimal artifact extension targets

The first execution-side extension points are likely to be:

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact` when execution is allowed
- a future blocked-run or policy-gate artifact when execution is denied upstream

## Rights-critical requirement

For rights-critical domains, permissive inference is not acceptable.

If Agentplane cannot recover the upstream promotion state and explanation context, it should treat the request as non-promotable for this slice.

## Follow-on implementation targets

A later implementation tranche should add:

1. a concrete verdict-envelope schema or adapter
2. a policy-gate artifact for blocked execution attempts
3. explicit reference preservation in replay-oriented artifacts
4. integration tests showing pass, fail, and missing-verdict behavior

## Non-goals for v0

This document does not require Agentplane to:
- duplicate Policy Fabric threshold logic
- own fixture expectations
- recalculate fit classifications locally
- replace upstream policy meaning with local heuristics
