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

## CHRONOS carrier passthrough (additive)

This bridge also accepts a second carried-object type: CHRONOS neuro-symbolic
carrier objects (per `sociosphere/docs/integration/neurosymbolic-chronos-alignment.md`).
This is the same seam widened to a second shape, not a second bridge — it reuses
the existing transport (declared refs on the `Bundle` spec, projected by the same
extraction functions that already project SourceOS bindings) and the same
consuming artifacts (`ValidationArtifact`, `RunArtifact`, `ReplayArtifact`).

A `Bundle` may optionally declare `spec.chronosCarrier`:

| Field | Meaning |
|---|---|
| `sourceEvidenceRef` | Reference to the upstream evidence the carrier grounds on |
| `methodFamily` | CHRONOS-owned method-family tag (e.g. NeurASP-style, dILP-style) |
| `claimStatus` | CHRONOS-owned claim status for the carrier |
| `validationStatus` | CHRONOS-owned validation status for the carrier |
| `nonAuthorityDeclaration` | Must be `true`: an explicit declaration that `agentplane` does not assert canonical authority over this carrier |
| `owningPlane` | The plane that owns this carrier's canonical definition (must not be `agentplane`) |
| `replayRef` | Reference agentplane can fold into its own `ReplayArtifact` |

`scripts/validate_bundle.py` fail-closes (like the existing SourceOS
image-production gate) when `spec.chronosCarrier` is declared but incomplete,
when `nonAuthorityDeclaration` is not `true`, or when `owningPlane` is
`agentplane` — i.e. an improperly-authorized carrier (one that omits or denies
its non-authority declaration, or that tries to route canonical ownership
through `agentplane`) is rejected at the bridge, the same way a malformed
SourceOS binding is rejected today.

`scripts/emit_run_artifact.py` and `scripts/emit_replay_artifact.py` project
whatever `chronosCarrier` fields are present into `RunArtifact.chronosCarrier`
and `ReplayArtifact.inputs.chronosCarrier` respectively, exactly as they already
do for `sourceosBindings`.

### Non-goals (CHRONOS carrier passthrough)
- `agentplane` does not take on carrier-schema or method-family taxonomy
  authority — `methodFamily`, `claimStatus`, and `validationStatus` values are
  passed through, not interpreted or enumerated here.
- This is a structural completeness/non-authority gate only, not cryptographic
  attestation or full authority/delegation reconstruction (see
  `docs/replay-boundary.md`).
- No canonical-schema authority moves into `sociosphere` or `agentplane`; it
  stays with Ontogenesis / `sourceos-spec` per CHRONOS's own definitions.
