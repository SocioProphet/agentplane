# Replay boundary

This document defines what the current public `ReplayArtifact` means in `agentplane` and, just as importantly, what it does **not** mean.

## Current replay contract

`ReplayArtifact` records the minimum inputs needed to attempt deterministic re-entry:

- bundle path
- bundle revision when available
- artifact directory
- policy pack reference and hash when available
- required secret names (never secret values)
- upstream workspace evidence references when available

This is an **input reconstruction contract**, not a claim that arbitrary side effects are automatically safe to reissue.

## What is replayed today

At the current public contract level, replay means:

1. re-identifying the bundle and bundle revision,
2. re-establishing the evidence directory,
3. recovering policy pointers and required secret names,
4. recovering upstream workspace evidence references,
5. providing enough information for a runner or operator to attempt a controlled re-run.

## What is not promised today

The current public contract does **not** promise all of the following:

- checkpoint-level continuation semantics,
- automatic side-effect suppression across arbitrary backends,
- cryptographic attestation of replay safety,
- full authority / delegation reconstruction,
- complete version-set pinning across runtime, model, connector, schema, and policy layers.

Those may be added later, but they are not implied by the current `ReplayArtifact` alone.

## Side-effect rule

Until a stronger replay model is published, external effects should be treated conservatively:

- effects may require explicit operator review before reissue,
- secret values must never be embedded in replay artifacts,
- policy and workspace evidence references should be reused rather than rediscovered,
- backends should prefer idempotent or evidence-first operations when possible.

## Relationship to receipts

The repo now also contains receipt-oriented examples under `examples/receipts/`.
Those examples enrich the broader runtime evidence story, but they do not replace the narrower `ReplayArtifact` contract.

## Relationship to governance

`docs/runtime-governance/control-matrix-integration.md` extends the evidence model toward row-level governance and incident linkage.
That document should be read as governance integration work layered above the current replay contract, not as proof that the replay contract already includes full control-loop semantics.
