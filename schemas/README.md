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
| [`agentic-pr-work-order.schema.v0.1.json`](agentic-pr-work-order.schema.v0.1.json) | `AgenticPRWorkOrder` | v0.1 | Issue-scoped work-order contract for agentic PR execution, review separation, policy refs, and ledger requirements. |
| [`action-proposal.schema.v0.1.json`](action-proposal.schema.v0.1.json) | `ActionProposal` | v0.1 | Agentplane action proposal contract for governed action intent, claims, and evidence refs. |
| [`action-admission.schema.v0.1.json`](action-admission.schema.v0.1.json) | `ActionAdmission` | v0.1 | Policy decision handoff and admission record for runtime execution boundary. |
| [`runtime-receipt.schema.v0.1.json`](runtime-receipt.schema.v0.1.json) | `RuntimeReceipt` | v0.1 | Runtime completion receipt for admitted actions with identity, hash, logs, timing, and status fields. |
| [`run-artifact.schema.v0.1.json`](run-artifact.schema.v0.1.json) | `RunArtifact` | v0.1 | Evidence record of a completed run. |
| [`replay-artifact.schema.v0.1.json`](replay-artifact.schema.v0.1.json) | `ReplayArtifact` | v0.1 | Inputs needed for deterministic replay. |
| [`session-artifact.schema.v0.1.json`](session-artifact.schema.v0.1.json) | `SessionArtifact` | v0.1 | Session-level lifecycle record (status, receipt/run/replay refs). |
| [`policy-decision-artifact.schema.v0.1.json`](policy-decision-artifact.schema.v0.1.json) | `PolicyDecisionArtifact` | v0.1 | AgentPlane evidence wrapper for SourceOS guardrail-fabric policy decisions. |
| [`stop-gate-artifact.schema.v0.1.json`](stop-gate-artifact.schema.v0.1.json) | `StopGateArtifact` | v0.1 | Evidence record for agent completion gates, false-done prevention, and human override posture. |
| [`promotion-artifact.schema.v0.1.json`](promotion-artifact.schema.v0.1.json) | `PromotionArtifact` | v0.1 | Evidence record of a bundle promotion event. |
| [`reversal-artifact.schema.v0.1.json`](reversal-artifact.schema.v0.1.json) | `ReversalArtifact` | v0.1 | Evidence record of a rollback/reversal event. |
| [`placement-decision.schema.v0.1.json`](placement-decision.schema.v0.1.json) | `PlacementDecision` | v0.1 | Executor placement decision and rejection record. |
| [`agent-machine-mount-evidence.schema.v0.1.json`](agent-machine-mount-evidence.schema.v0.1.json) | `AgentMachineMountEvidence` | v0.1 | Evidence record for SourceOS Agent Machine local data-plane mounts and optional TopoLVM placement metadata. |
| [`sourceos-context-tool-provider-evidence.schema.v0.1.json`](sourceos-context-tool-provider-evidence.schema.v0.1.json) | `SourceOSContextToolProviderEvidence` | v0.1 | Evidence record registering `sourceos-context` as a constrained, non-mutating local tool provider. |
| [`office-artifact-evidence.schema.v0.1.json`](office-artifact-evidence.schema.v0.1.json) | `OfficeArtifactEvidence` | v0.1 | Evidence record for Prophet Workspace OfficeArtifact generation, inspection, conversion, review, or publishing actions. |
| [`network-door-plan-evidence.schema.v0.1.json`](network-door-plan-evidence.schema.v0.1.json) | `NetworkDoorPlanEvidence` | v0.1 | Evidence record for non-mutating SourceOS Network Door route, firewall, mesh, and BYOM planning. |
| [`external-model-provider-route-evidence.schema.v0.1.json`](external-model-provider-route-evidence.schema.v0.1.json) | `ExternalModelProviderRouteEvidence` | v0.1 | Evidence record for BYOM or enterprise external model provider route planning under policy. |
| [`native-assistant-bridge-evidence.schema.v0.1.json`](native-assistant-bridge-evidence.schema.v0.1.json) | `NativeAssistantBridgeEvidence` | v0.1 | Evidence record for native assistant bridge planning across Apple App Intents/Siri/Shortcuts, Android, Windows, browser, MCP, or other host/device bridges. |
| [`policy-fabric-verdict-envelope.schema.v0.1.json`](policy-fabric-verdict-envelope.schema.v0.1.json) | `PolicyFabricVerdictEnvelope` | v0.1 | Execution-side envelope for consuming governed Policy Fabric promotion verdicts. |
| [`office-artifact-evidence.schema.v0.1.json`](office-artifact-evidence.schema.v0.1.json) | `OfficeArtifactEvidence` | v0.1 | Evidence record for Prophet Workspace OfficeArtifact generation, inspection, conversion, review, or publishing actions. |

---

## Bundle schema (`bundle.schema.v0.1.json`)

The bundle schema defines the contract for `bundle.json` files. Validated by `scripts/validate_bundle.py`.

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
| `spec.vm.modulePath` | string | Path to NixOS module entry (e.g., `vm.nix`) |
| `spec.vm.backendIntent` | enum | One of: `qemu`, `microvm`, `lima-process`, `fleet` |
| `spec.policy.maxRunSeconds` | integer | 5–3600 |
| `spec.secrets` | object | Secret refs only — never inline values |
| `spec.artifacts.outDir` | string | Directory where evidence artifacts are written |
| `spec.smoke.script` | string | Path to smoke test script |

### License policy constraint

`metadata.licensePolicy.allowAGPL` must be `false`. This is validated at bundle validation time and cannot be overridden. See [ADR-0001](../docs/adr/0001-no-agpl-dependencies.md).

---

## Agentic PR Work Order (`agentic-pr-work-order.schema.v0.1.json`)

`AgenticPRWorkOrder` is the issue-scoped contract for agent-produced pull requests. It records the objective, authority split, expected files, denied paths, validation requirements, review checklist, PR output requirements, policy references, and ledger fields for an implementation tranche.

The contract exists to keep implementation agents bounded. An implementation agent may propose a draft PR, but the work order requires separate review and merge-gate authority.

Key fields:

| Field | Purpose |
|---|---|
| `spec.authority.implementationAgent` | Actor allowed to produce a bounded patch. |
| `spec.authority.reviewAgent` | Actor or role responsible for adversarial review. |
| `spec.authority.mergeGate` | Policy gate responsible for merge decision. |
| `spec.authority.separationOfDuties` | Must be `true`; implementation, review, and merge authority stay separate. |
| `spec.scope.expectedFiles` | File set expected from the issue-scoped tranche. |
| `spec.scope.deniedPaths` | Generated dependency trees, virtual environments, caches, and build outputs that must not appear in a PR. |
| `spec.validation.requiredCommands` | Commands or checks the PR must report. |
| `spec.output.requiredPrSections` | Required PR body sections such as validation, known gaps, self-critique, and policy evidence. |
| `spec.policyRefs.diffHygieneGate` | Policy Fabric gate or issue that evaluates pre-review diff hygiene. |
| `spec.ledger.fields` | Minimal fields needed for post-run or post-merge ledger evidence. |

Validated by `tools/validate_agentic_pr_work_order.py`.

---

## Patch fragment (`bundle.schema.patch.json`)

This file is a **JSON Merge Patch-style fragment** staging new `spec` fields for future agent-runtime bundles. It is not a complete schema and is not yet enforced by `scripts/validate_bundle.py`.

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

These fields will be promoted to a `bundle.schema.v0.2.json` once the agent-runtime integration is ready. Do not use them in production bundles until they are promoted.

---

## Artifact schemas

### ActionProposal (`action-proposal.schema.v0.1.json`)

Defines the pre-execution proposal envelope from `AgentIntent`:

- action intent + target references;
- `Claim` refs for intent and expected effects;
- `Evidence` refs;
- optional prior-action `VectorCandidate` retrieval records that must remain `candidateOnly: true` and `admissionAuthority: false`.

### ActionAdmission (`action-admission.schema.v0.1.json`)

Defines policy-to-runtime admission handoff:

- proposal reference;
- policy decision reference (`PolicyDecisionArtifact` compatible);
- admitted runtime boundary (`nodeRef`, `runtimeRef`, `runtimeProfileRef`, `sandboxProfileRef`) for admitted actions;
- denied records with reason for non-admitted actions.

### RuntimeReceipt (`runtime-receipt.schema.v0.1.json`)

Defines required receipt fields for admitted runtime work:

- agent identity;
- node/runtime identity;
- runtime/sandbox profile refs;
- input/output hashes;
- logs reference;
- policy decision reference;
- start and end times;
- final status.

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

### PolicyDecisionArtifact (`policy-decision-artifact.schema.v0.1.json`)

Wraps a `sourceos.guardrail.decision.v0.1` decision emitted by `SocioProphet/guardrail-fabric` so AgentPlane can treat policy decisions as first-class evidence.

It records:

- AgentPlane session/task refs;
- guardrail source system, adapter, version, repo, and commit;
- embedded SourceOS policy decision artifact;
- AgentPlane result interpretation (`allow`, `blocked`, `needs_human`, `redacted`, `quarantined`, or `deferred`);
- decision log, tool event, redaction, and human override refs;
- optional governance context.

AgentPlane should not reimplement guardrail policy logic. It should ingest and preserve the decision, then use the interpreted result for stop gates and runtime transitions.

### SourceOSContextToolProviderEvidence (`sourceos-context-tool-provider-evidence.schema.v0.1.json`)

Registers `sourceos-context` as a constrained local tool provider.

It records:

- provider identity (`smart-tree-context-provider`);
- policy profile (`sourceos.repo_context.read_only`);
- allowed and denied capabilities;
- integration targets: Lampstand, Sherlock, Memory Mesh, and Policy Fabric;
- side-effect flags proving the provider is non-mutating by default;
- the requirement that Lampstand publishing needs an explicit flag.

This evidence does not dispatch a run. It is a registration/control-plane artifact for later AgentPlane routing.

### OfficeArtifactEvidence (`office-artifact-evidence.schema.v0.1.json`)
### StopGateArtifact (`stop-gate-artifact.schema.v0.1.json`)

Records the evidence behind an agent completion gate. Stop gates prevent false-done completion by requiring branch, commit, push, PR, CI, policy, summary, and human-review evidence where applicable.

It records:

- session/task refs;
- gate identity and policy ref;
- final result (`pass`, `fail`, `needs_human`, `waived`, or `not_applicable`);
- per-check result, reason, remediation, evidence refs, and related policy decision refs;
- optional human override ref;
- related policy decision, run, replay, PR, CI, and summary artifact refs.

A stop gate that fails should produce actionable remediation rather than a generic blocked state.

### PolicyFabricVerdictEnvelope (`policy-fabric-verdict-envelope.schema.v0.1.json`)

Consumed by the interim `scripts/validate_bundle_with_policy_fabric_gate.py` wrapper.

It records the upstream Policy Fabric promotion verdict needed by AgentPlane execution admission:

- policy bundle identity;
- target domain and optional bundle/lane context;
- promote or block result;
- fit classification;
- failed predicates and reason strings;
- threshold context;
- upstream verdict artifact references.

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
| `inputs.bundleRev` | string|null | Git commit SHA of the bundle |
| `inputs.bundleRev` | string\|null | Git commit SHA of the bundle |
| `inputs.bundleRev` | string or null | Git commit SHA of the bundle |
| `inputs.artifactDir` | string | Absolute path to the artifact output directory |

Optional inputs: `policyPackRef`, `policyPackHash`, `secretsRequired`, `upstreamArtifacts.*`.

### SessionArtifact (`session-artifact.schema.v0.1.json`)

Records the lifecycle of an agent session. `sessionRef` must match the pattern `urn:srcos:session:*`.

### PromotionArtifact (`promotion-artifact.schema.v0.1.json`)

Records a bundle promotion event. `promotionReceiptRef` must match `urn:srcos:receipt:promotion:*`.

### ReversalArtifact (`reversal-artifact.schema.v0.1.json`)

Records a rollback/reversal event. `sourcePromotionReceiptRef` must match `urn:srcos:receipt:promotion:*`.

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
  versioned schema.
  versioned schema.
- **Breaking changes** to a schema require a new version file (e.g., `v0.2`). Do not edit a released schema in place.
- **Additive, backward-compatible changes** (new optional fields) may be made in a minor version increment.
- The validator (`scripts/validate_bundle.py`) must be updated when a new bundle schema version is introduced.
- Patch fragments (`.patch.json`) are staging areas; they are not enforced until promoted to a versioned schema.
