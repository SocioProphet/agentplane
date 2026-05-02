# schemas

JSON Schemas for agentplane Bundle and artifact types.

All schemas use [JSON Schema Draft 2020-12](https://json-schema.org/specification).

---

## Schema index

| File | Kind | Version | Description |
|---|---|---|---|
| [`bundle.schema.v0.1.json`](bundle.schema.v0.1.json) | `Bundle` | v0.1 | Bundle manifest schema. Defines the structure of `bundle.json`. |
| [`bundle.schema.patch.json`](bundle.schema.patch.json) | patch fragment | — | Staged future fields for agent-runtime bundles (not yet enforced). |
| [`broker-execution-bundle.schema.v0.1.json`](broker-execution-bundle.schema.v0.1.json) | `BrokerExecutionBundle` | v0.1 | Broker validation/smoke/continuity/exit/cost-meter execution bundle contract. |
| [`run-artifact.schema.v0.1.json`](run-artifact.schema.v0.1.json) | `RunArtifact` | v0.1 | Evidence record of a completed run. |
| [`replay-artifact.schema.v0.1.json`](replay-artifact.schema.v0.1.json) | `ReplayArtifact` | v0.1 | Inputs needed for deterministic replay. |
| [`session-artifact.schema.v0.1.json`](session-artifact.schema.v0.1.json) | `SessionArtifact` | v0.1 | Session-level lifecycle record (status, receipt/run/replay refs). |
| [`promotion-artifact.schema.v0.1.json`](promotion-artifact.schema.v0.1.json) | `PromotionArtifact` | v0.1 | Evidence record of a bundle promotion event. |
| [`reversal-artifact.schema.v0.1.json`](reversal-artifact.schema.v0.1.json) | `ReversalArtifact` | v0.1 | Evidence record of a rollback/reversal event. |
| [`placement-decision.schema.v0.1.json`](placement-decision.schema.v0.1.json) | `PlacementDecision` | v0.1 | Executor placement decision and rejection record. |
| [`agent-machine-mount-evidence.schema.v0.1.json`](agent-machine-mount-evidence.schema.v0.1.json) | `AgentMachineMountEvidence` | v0.1 | Evidence record for SourceOS Agent Machine local data-plane mounts and optional TopoLVM placement metadata. |

---

## Bundle schema (`bundle.schema.v0.1.json`)

The bundle schema defines the contract for `bundle.json` files. Validated by
`scripts/validate_bundle.py`.

### Required fields

| Path | Type | Notes |
|---|---|---|
| `apiVersion` | string | Must be `agentplane.socioprophet.org/v0.1` |
| `kind` | string | Must be `Bundle` |
| `metadata.name` | string | Pattern: `^[a-z0-9][a-z0-9-]{1,62}$` |
| `metadata.version` | string | Semver recommended |
| `metadata.createdAt` | string | ISO 8601 datetime |
| `spec.vm.modulePath` | string | Path to NixOS module entry or adapter module path |
| `spec.vm.backendIntent` | enum | One of: `qemu`, `microvm`, `lima-process`, `fleet`, `agent-machine` |
| `spec.policy.maxRunSeconds` | integer | 5–3600 |
| `spec.secrets` | object | Secret refs only — never inline values |
| `spec.artifacts.outDir` | string | Directory where evidence artifacts are written |
| `spec.smoke.script` | string | Path to smoke test script |

### License policy constraint

`metadata.licensePolicy.allowAGPL` must be `false`. This is validated at bundle
validation time and cannot be overridden. See [ADR-0001](../docs/adr/0001-no-agpl-dependencies.md).

### Agent Machine binding

`spec.agentMachine` is an optional SourceOS Agent Machine binding. It references canonical contracts in `SourceOS-Linux/sourceos-spec` rather than redefining local mount policy inside AgentPlane.

Key fields:

| Field | Purpose |
|---|---|
| `profileRef` | Agent Machine profile reference. |
| `localDataPlaneRef` | `AgentMachineLocalDataPlane` reference. |
| `mountPolicyRef` | `AgentMachineMountPolicy` reference. |
| `secureHostInterfaceRef` | Secure Host Interface profile/grant reference. |
| `topolvmPlacementProfileRef` | Optional `TopoLVMPlacementProfile` reference for cluster-local mode. |
| `workspaceId` | Local/cluster workspace identity. |
| `toolSurfaceRefs` | Agent tool surfaces such as OpenCLAW/OpenClaw, Hermes, Codex, Claude Code, local shell, GitHub bot, or CI bot. |

---

## Patch fragment (`bundle.schema.patch.json`)

This file is a **JSON Merge Patch-style fragment** staging new `spec` fields for future
agent-runtime bundles. It is not a complete schema and is not yet enforced by
`scripts/validate_bundle.py`.

### Staged fields

| Field | Type | Purpose |
|---|---|---|
| `spec.sessionPolicyRef` | string | Reference to a session-level policy document |
| `spec.skillRefs` | string[] | References to agent skill definitions |
| `spec.memoryNamespace` | string | Memory namespace for the agent session |
| `spec.worktreeStrategy` | enum | How to handle the git worktree: `none`, `existing`, `create-temp`, `named` |
| `spec.rolloutFlags` | string[] | Feature/rollout flags for the bundle |
| `spec.telemetrySink` | string | Telemetry destination URI |
| `spec.receiptSchemaVersion` | string | Version of the MAIPJ run receipt schema to validate against |

These fields will be promoted to a `bundle.schema.v0.2.json` once the agent-runtime integration
is ready. Do not use them in production bundles until they are promoted.

---

## Artifact schemas

### RunArtifact (`run-artifact.schema.v0.1.json`)

Written by `scripts/emit_run_artifact.py` and by `runners/qemu-local.sh`.

| Required field | Type | Notes |
|---|---|---|
| `kind` | const | `"RunArtifact"` |
| `bundle` | string | `"<name>@<version>"` |
| `capturedAt` | string | ISO 8601 datetime |
| `lane` | enum | `"staging"` or `"prod"` |
| `executor` | string | Chosen executor name |
| `backendIntent` | enum | `qemu`, `microvm`, `lima-process`, `fleet` |
| `status` | enum | `"success"` or `"failure"` |
| `exitCode` | integer | Process exit code |

Optional: `bundlePath`, `stdoutRef`, `stderrRef`, `upstreamArtifacts.*`.

### AgentMachineMountEvidence (`agent-machine-mount-evidence.schema.v0.1.json`)

Emitted by Agent Machine executor adapters or imported from `sourceosctl agent-machine mounts ...` evidence records.

It records:

- `localDataPlaneRef` and `mountPolicyRef` from SourceOS contracts;
- storage backend (`podman-machine-bind`, `native-bind`, `wsl-bind`, `topolvm-local-pv`, etc.);
- mount path classes (`code`, `documents`, `downloads`, `cache`, `artifacts`, `media`, `app-bridge`);
- scoped browser download evidence;
- denied mount attempts;
- optional TopoLVM node/PVC/PV metadata;
- redaction summary.

Browser downloads are intentionally represented as a distinct path class. Downloaded artifacts should be hashed, and promotion into code or document-output space should emit separate evidence.

### ReplayArtifact (`replay-artifact.schema.v0.1.json`)

Written by `scripts/emit_replay_artifact.py`.

| Required field | Type | Notes |
|---|---|---|
| `kind` | const | `"ReplayArtifact"` |
| `bundle` | string | `"<name>@<version>"` |
| `capturedAt` | string | ISO 8601 datetime |
| `executor` | string | Chosen executor name |
| `backendIntent` | enum | `qemu`, `microvm`, `lima-process`, `fleet` |
| `inputs.bundlePath` | string | Path to the bundle directory |
| `inputs.bundleRev` | string\|null | Git commit SHA of the bundle |
| `inputs.artifactDir` | string | Absolute path to the artifact output directory |

Optional inputs: `policyPackRef`, `policyPackHash`, `secretsRequired`, `upstreamArtifacts.*`.

### SessionArtifact (`session-artifact.schema.v0.1.json`)

Records the lifecycle of an agent session. `sessionRef` must match the pattern
`urn:srcos:session:*`.

### PromotionArtifact (`promotion-artifact.schema.v0.1.json`)

Records a bundle promotion event. `promotionReceiptRef` must match
`urn:srcos:receipt:promotion:*`.

### ReversalArtifact (`reversal-artifact.schema.v0.1.json`)

Records a rollback/reversal event. `sourcePromotionReceiptRef` must match
`urn:srcos:receipt:promotion:*`.

---

## Versioning policy

- Schemas are versioned with a `vX.Y` suffix in the filename.
- **Breaking changes** to a schema require a new version file (e.g., `v0.2`). Do not edit a
  released schema in place.
- **Additive, backward-compatible changes** (new optional fields) may be made in a minor
  version increment.
- The validator (`scripts/validate_bundle.py`) must be updated when a new bundle schema version
  is introduced.
- Patch fragments (`.patch.json`) are staging areas; they are not enforced until promoted to a
  versioned schema.
