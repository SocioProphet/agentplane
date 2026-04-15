# Promotion evidence checklist

This checklist defines the minimum evidence expected before advancing a SourceOS artifact set through the shared control-plane channels.

## Shared terms

Reusable channel and capability terms are defined in `SocioProphet/socioprophet-agent-standards`.

This repository defines the lifecycle and evidence requirements attached to those terms.

## dev -> candidate

Before advancing from `dev` to `candidate`, the control plane should have:

- a channel manifest for the target artifact set
- a source revision reference
- a realizable host/image/build artifact reference
- a named evaluation bundle or score bundle reference
- a rollback reference
- capability versions or capability map
- evidence that the target artifact completed the intended smoke/build checks

## candidate -> stable

Before advancing from `candidate` to `stable`, the control plane should have all of the above plus:

- evidence of candidate-level integration validation
- explicit approval identity or approved-by set
- no unresolved rollback-blocking failure from the evaluation bundle
- a stable rollback target reference

## Practical interpretation

The checklist is intentionally minimal.

`agentplane` should continue to refine how these evidence items are produced, but a promotion event should not be treated as complete unless these references exist and can be inspected or replayed.
