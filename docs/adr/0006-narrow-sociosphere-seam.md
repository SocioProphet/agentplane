# ADR-0006: Intentionally narrow sociosphere-agentplane seam

Date: 2026-04-05  
Status: Accepted

## Context

`sociosphere` (workspace controller) and `agentplane` (execution control plane) are separate
repositories with separate owners. Without an explicit interface constraint, each system could
grow to depend on internal details of the other, creating coupling that makes them hard to
evolve independently.

Several integration patterns were considered:

1. **Shared library** — A common package used by both repos. Creates a build-time dependency and
   forces synchronized versioning.
2. **Event bus** — A pub/sub channel where both repos produce and consume freely. Flexible but
   hard to audit and easy to misuse.
3. **Narrow artifact seam** — `sociosphere` emits a small set of normalized artifacts and
   optionally generates a valid Bundle; `agentplane` consumes the bundle and preserves its own
   evidence. No shared runtime dependency.

## Decision

The seam between `sociosphere` and `agentplane` is intentionally narrow and artifact-based:

- `sociosphere` emits four artifact types: `WorkspaceInventoryArtifact`,
  `LockVerificationArtifact`, `TaskRunArtifact`, `ProtocolCompatibilityArtifact`.
- `sociosphere` may generate a valid Bundle that `agentplane` consumes.
- `agentplane` receives references to upstream artifacts via four environment variables
  (see [ADR-0003](0003-sociosphere-owns-workspace-truth.md)).
- `agentplane` produces its own evidence artifacts (`ValidationArtifact`, `PlacementDecision`,
  `RunArtifact`, `ReplayArtifact`) independently.
- Neither system re-scans the other's domain.

See [docs/sociosphere-bridge.md](../sociosphere-bridge.md) for the full contract.

## Consequences

- **Positive:** Both repos can evolve independently as long as they honour the artifact interface.
- **Positive:** The seam is easy to audit: four env vars and four artifact types.
- **Positive:** No shared runtime dependency to synchronize.
- **Negative:** The env-var protocol is implicit and must be explicitly documented to avoid
  accidental omission in new runner backends.
- **Negative:** If the artifact interface needs to change, both repos must be updated in a
  coordinated fashion, even though there is no shared code.
