# Semantic-proof consumer bridge v0.1

## Purpose

This note defines the narrow `agentplane` consumer/import boundary for the semantic-proof / replay interoperability work.

`agentplane` is not the canonical schema or transport repository for this work. It is the runtime consumer lane that:

- imports proof-bearing references from shared standards surfaces
- binds them into receipt/evidence/replay flows
- exposes verifier hook points for runtime evidence and replay materialization

## Why this belongs here

The current repository already owns:
- run / replay artifact schemas
- live receipt integration planning
- runtime governance import surfaces
- control-matrix import and enforcement notes

The semantic-proof work should therefore land here only as runtime consumption and evidence-binding material.

## Canonical homes outside this repo

- `socioprophet-standards-storage` — shared proof schemas, vocabulary, fixture canon
- `TriTRPC` — deterministic transport-facing bridge and method/fixture alignment
- `cairnpath-mesh` — replay/materialize semantics and worked replay fixtures

## Consumer responsibilities in `agentplane`

### 1. Receipt binding
Runtime receipts should be able to carry:
- proof references
- verifier status
- replay handle / cairn reference
- worldview or semantic-surface identifiers where applicable

### 2. Verifier hook points
`agentplane` should expose a narrow verifier invocation surface for:
- inclusion proof checks over imported semantic artifacts
- replay-materialization proof checks
- explicit separation of transport failure from proof failure

### 3. Runtime import posture
Imported semantic-proof assets should be treated as versioned external bundles, not redefined locally.

## Initial hook points

- receipt assembly path
- replay manifest materialization path
- runtime-governance evidence append path

## Deliberate exclusions

This bridge note does not add:
- canonical proof schemas
- canonical vocabulary
- lowering logic
- transport method definitions
- cairn/materialize validator ownership

## Follow-on

1. add a small imported-bundle manifest under `policy/imports/semantic-proof/`
2. wire verifier outcomes into receipt and replay artifact examples
3. bind imported proof refs to the first local-hybrid runtime path once the shared standards slice stabilizes
