# SourceOS substrate integration

This document defines how `agentplane` participates in the SourceOS workstation substrate lane.

## Role of agentplane

`agentplane` is not the substrate implementation and not the canonical contract registry.

For the SourceOS workstation lane it owns:

- stage bundle definition,
- stage execution environment,
- smoke validation execution,
- evidence and replay artifacts for stage runs.

## Upstream dependencies

The SourceOS substrate lane depends on:

- `SociOS-Linux/SourceOS` — host/substrate implementation
- `SourceOS-Linux/sourceos-spec` — typed boot/storage/staged deployment contracts
- `SociOS-Linux/workstation-contracts` — workstation lane contract and conformance

## Current bundle

The first substrate-facing bundle is:

- `bundles/sourceos-asahi-stage/`

It is intended to stage a Fedora Asahi + Nix control-plane candidate with mounted config/state/evidence paths and emit stage-health evidence.

## Expected evidence posture

At minimum the bundle should yield:

- successful validation of mounted inputs,
- stage smoke result,
- artifact directory outputs usable by later promotion logic.

## Boundary rule

`agentplane` consumes contract shapes and substrate inputs; it must not become the canonical home for SourceOS substrate policy or workstation contract definitions.
