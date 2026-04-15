# SourceOS local control node and Node Commander integration (v0)

## Purpose

This note records how the current SourceOS / SociOS Linux local control-node work should bind into `agentplane`.

`agentplane` remains the downstream execution control plane. It is not the canonical home for host bootstrap or workstation profile semantics. But it is the correct place to capture how those host-side surfaces feed bundle validation, placement, run, replay, and promotion evidence.

## Current upstream split

- `SourceOS-Linux/sourceos-spec`
  - canonical typed-contract and ADR lane
- `SociOS-Linux/source-os`
  - workstation/bootstrap and profile application lane
- `SocioProphet/agentplane`
  - execution control plane, executor selection, evidence and replay
- `SocioProphet/prophet-platform`
  - deployable runtime/service implementation lane

This file documents the `agentplane` seam only.

## What the local control node already proves

The current operator-node prototype has already demonstrated:

- declarative macOS control-node configuration via nix-darwin
- OCI build/push/run using Podman
- local `Node Commander` image staging
- a user-scoped runtime envelope suitable for local-first operation

That work is not yet a production runtime, but it is enough to define the downstream `agentplane` seam.

## Agentplane responsibilities in this slice

For the local-first control-node / image-promotion slice, `agentplane` is responsible for:

1. **Validate** candidate execution bundles and emit `ValidationArtifact`.
2. **Place** work according to local-first / trusted-private / attested-fog / explicit-cloud ordering.
3. **Run** on the selected executor and emit `RunArtifact`.
4. **Replay** with enough evidence to deterministically inspect the decision and execution path.
5. **Consume** promotion-gate evidence from the operator-side control node without becoming the canonical source of those contract meanings.

## What `agentplane` should consume from the control node

The control node / Node Commander side is expected to hand off at least the following:

- candidate build identity
- build provenance digest(s)
- target image or profile identity
- local validation scenario outputs
- promotion-gate decision inputs
- promotion-gate decision result
- references to local state, logs, or receipts that belong in replay/evidence artifacts

`agentplane` should consume those as downstream inputs and emit its own runtime/evidence artifacts. It should not redefine the contract meanings owned by `sourceos-spec`.

## Immediate implementation guidance

This repo should treat the local control-node lane as:

- a **downstream executor/integration surface**
- compatible with Podman/OCI-based local execution
- compatible with a future Linux/NixOS builder path
- evidence-forward and replay-friendly

This implies the next `agentplane` work items should be additive and narrow:

1. document a local-control-node executor/inventory example
2. add a promotion-gate evidence consumption note or fixture
3. add a runner/integration note for OCI-backed local command execution where appropriate
4. keep host bootstrap details out of canonical `agentplane` contract ownership

## Non-goals for this repo

This repo should not become the home for:

- nix-darwin host bootstrap instructions
- workstation shell/profile management
- Docker helper or registry-helper implementation details
- canonical contract definitions for `ControlNodeProfile`, `NodeCommanderRuntime`, or `ImagePromotionGate`

Those belong elsewhere in the repo topology.

## Why this note exists now

`agentplane` is active and already carrying repository-placement and runtime-governance work on `main`. Capturing the local control-node seam here avoids the current implementation work becoming disconnected from the execution/evidence plane that will ultimately consume it.
