# Fleet Model

`agentplane` currently uses a local-first fleet shape, but the inventory should already reflect the roles we intend to scale:

- **builders** — systems that can perform Nix and image builds
- **executors** — systems that can execute bundles
- **selectionPolicy** — repo-local placement policy that determines which executor should be preferred

## Why this split matters

The previous inventory shape treated a single host as both implicit builder and executor without naming the distinction. That is workable for Lima-based development, but it obscures the control-plane semantics we need once fleet nodes diversify.

A typed fleet inventory lets us reason about:

- whether a host can build images
- whether a host can execute a requested backend
- whether a host is enabled and healthy enough to receive work
- whether a placement was made because a node was preferred or because every other candidate was rejected

## Current local-first path

The current default inventory keeps `lima-nixbuilder` in both roles:

- as the default **builder** for Linux-target Nix builds from non-Linux control-plane hosts
- as the default **executor** for `lima-process` runs

This preserves existing behavior while making the inventory semantics explicit.

## Selection expectations

Placement should reject candidates explicitly for:

- disabled state
- degraded / drained / offline health
- platform mismatch
- unsupported backend
- missing KVM for VM backends
- SSH reachability failure

Those rejection reasons belong in the `PlacementDecision` evidence so scheduling stays explainable.

## Compatibility note

`/etc/nix/machines` remains a legacy fallback for host-local builder configuration. It should not be treated as the long-term fleet source of truth.
