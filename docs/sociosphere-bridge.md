# Sociosphere Bridge Note

`agentplane` is the execution control plane.
`sociosphere` is the workspace controller.

The seam is intentionally narrow:
- `sociosphere` emits normalized workspace artifacts (`WorkspaceInventoryArtifact`, `LockVerificationArtifact`, `TaskRunArtifact`, `ProtocolCompatibilityArtifact`)
- `sociosphere` may generate a valid `Bundle`
- `agentplane` consumes the bundle and preserves execution-plane evidence (`ValidationArtifact`, `PlacementDecision`, `RunArtifact`, `ReplayArtifact`)

## Upstream artifact references
When available, downstream scripts may receive upstream workspace evidence through environment variables:
- `SOCIOSPHERE_WORKSPACE_INVENTORY_REF`
- `SOCIOSPHERE_LOCK_VERIFICATION_REF`
- `SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF`
- `SOCIOSPHERE_TASK_RUN_REFS` (comma-separated)

These are references only. `agentplane` must not rescan the workspace to rediscover the same facts.

## Intended run order
1. `sociosphere` validates workspace composition and emits upstream artifacts.
2. `sociosphere` generates a valid `Bundle`.
3. `agentplane` validates the bundle.
4. `agentplane` selects an executor.
5. runner backend performs the run.
6. `agentplane` emits `RunArtifact` and `ReplayArtifact` into the bundle artifact directory.

## Non-goals
- `agentplane` is not the source of truth for repo inventory or lock drift.
- `sociosphere` is not the source of truth for executor placement or runtime replay artifacts.
