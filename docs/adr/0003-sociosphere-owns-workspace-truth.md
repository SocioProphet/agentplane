# ADR-0003: sociosphere owns workspace truth

Date: 2026-04-05  
Status: Accepted

## Context

During a governed execution, both `sociosphere` (workspace controller) and `agentplane`
(execution control plane) have access to workspace-related information. A question arose: should
`agentplane` re-scan the workspace to independently verify its composition, or should it trust
the artifacts emitted by `sociosphere`?

Re-scanning would duplicate effort, create divergence risk, and break the clean separation of
concerns between the two systems.

## Decision

`sociosphere` is the source of truth for workspace composition and lock verification.
`agentplane` must not re-scan the workspace to rediscover facts that `sociosphere` has already
established.

`agentplane` receives workspace evidence through four environment variables:

- `SOCIOSPHERE_WORKSPACE_INVENTORY_REF`
- `SOCIOSPHERE_LOCK_VERIFICATION_REF`
- `SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF`
- `SOCIOSPHERE_TASK_RUN_REFS` (comma-separated)

These references are passed through to `RunArtifact.upstreamArtifacts` and
`ReplayArtifact.inputs.upstreamArtifacts` without modification.

See [docs/sociosphere-bridge.md](../sociosphere-bridge.md) and
[docs/integration/sociosphere.md](../integration/sociosphere.md).

## Consequences

- **Positive:** Clean separation of concerns. Each system owns what it knows best.
- **Positive:** Eliminates double-counting and divergence between workspace views.
- **Positive:** `agentplane` stays lean — it does not need workspace-scanning logic.
- **Negative:** `agentplane`'s receipt depends on `sociosphere` emitting valid artifacts. If
  `sociosphere` emits incorrect workspace info, `agentplane` will faithfully propagate the error.
- **Negative:** The env-var integration is an implicit protocol; it must be explicitly documented
  (this ADR and [docs/integration/sociosphere.md](../integration/sociosphere.md)) to avoid
  accidental omission.
