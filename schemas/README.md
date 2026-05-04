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
| [`run-artifact.schema.v0.1.json`](run-artifact.schema.v0.1.json) | `RunArtifact` | v0.1 | Evidence record of a completed run. |
| [`replay-artifact.schema.v0.1.json`](replay-artifact.schema.v0.1.json) | `ReplayArtifact` | v0.1 | Inputs needed for deterministic replay. |
| [`session-artifact.schema.v0.1.json`](session-artifact.schema.v0.1.json) | `SessionArtifact` | v0.1 | Session-level lifecycle record (status, receipt/run/replay refs). |
| [`promotion-artifact.schema.v0.1.json`](promotion-artifact.schema.v0.1.json) | `PromotionArtifact` | v0.1 | Evidence record of a bundle promotion event. |
| [`reversal-artifact.schema.v0.1.json`](reversal-artifact.schema.v0.1.json) | `ReversalArtifact` | v0.1 | Evidence record of a rollback/reversal event. |
| [`placement-decision.schema.v0.1.json`](placement-decision.schema.v0.1.json) | `PlacementDecision` | v0.1 | Executor placement decision and rejection record. |
| [`agent-machine-mount-evidence.schema.v0.1.json`](agent-machine-mount-evidence.schema.v0.1.json) | `AgentMachineMountEvidence` | v0.1 | Evidence record for SourceOS Agent Machine local data-plane mounts and optional TopoLVM placement metadata. |
| [`office-artifact-evidence.schema.v0.1.json`](office-artifact-evidence.schema.v0.1.json) | `OfficeArtifactEvidence` | v0.1 | Evidence record for Prophet Workspace OfficeArtifact generation, inspection, conversion, review, or publishing actions. |
| [`network-door-plan-evidence.schema.v0.1.json`](network-door-plan-evidence.schema.v0.1.json) | `NetworkDoorPlanEvidence` | v0.1 | Evidence record for non-mutating SourceOS Network Door route, firewall, mesh, and BYOM planning. |
| [`external-model-provider-route-evidence.schema.v0.1.json`](external-model-provider-route-evidence.schema.v0.1.json) | `ExternalModelProviderRouteEvidence` | v0.1 | Evidence record for BYOM or enterprise external model provider route planning under policy. |
| [`native-assistant-bridge-evidence.schema.v0.1.json`](native-assistant-bridge-evidence.schema.v0.1.json) | `NativeAssistantBridgeEvidence` | v0.1 | Evidence record for native assistant bridge planning across Apple App Intents/Siri/Shortcuts, Android, Windows, browser, MCP, or other host/device bridges. |

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

### OfficeArtifactEvidence (`office-artifact-evidence.schema.v0.1.json`)

Emitted by Office Plane executor adapters or imported from `sourceosctl office ...` evidence records.

It records:

- `workroomId` and `artifactId` from `SocioProphet/prophet-workspace` OfficeArtifact contracts;
- artifact type and format for documents, sheets, slide decks, PDFs, mail drafts, calendar items, task lists, notes, and media assets;
- operation (`plan`, `generate`, `inspect`, `convert`, `render`, `analyze`, `review`, `promote`, `publish`, or `send-draft`);
- backend (`libreoffice`, `collabora`, `onlyoffice`, `microsoft-graph`, `google-workspace`, `sourceos-native`, or `manual`);
- artifact hashes and derived artifact refs;
- conversion metadata;
- review state;
- side-effect flags for email, external publish, and calendar modification;
- policy refs and redaction summary.

Email sending and external publishing should remain explicit policy-gated side effects. Generated mail should normally be represented as a draft artifact before send.

### NetworkDoorPlanEvidence (`network-door-plan-evidence.schema.v0.1.json`)

Emitted by Network Door executor adapters or imported from `sourceosctl network ...` plan records.

It records:

- NetworkAccessProfile references;
- user and enterprise firewall binding refs;
- optional mesh binding refs;
- BYOM/external model provider refs;
- route decision and scope;
- hash-only destination evidence;
- enterprise/user precedence posture;
- side-effect flags proving the plan did not mutate firewall or mesh state;
- policy refs and redaction summary.

Mesh binding and firewall binding should be represented as complementary policy layers, not interchangeable controls.

### ExternalModelProviderRouteEvidence (`external-model-provider-route-evidence.schema.v0.1.json`)

Emitted by external model provider route adapters or imported from `sourceosctl network provider ...` plan records.

It records:

- provider refs and provider class;
- owner (`user`, `enterprise`, `workspace`, `tenant`, or `device`);
- NetworkAccessProfile, FirewallBindingProfile, and optional MeshBindingProfile refs;
- Model Router binding refs and route target;
- auth reference posture without inline credentials;
- prompt hash-only evidence;
- prompt egress policy;
- provider health metadata when explicitly checked;
- side-effect flags for provider contact and prompt transmission.

Provider credentials must remain references. Do not inline tokens, API keys, base credentials, or secrets in evidence records.

### NativeAssistantBridgeEvidence (`native-assistant-bridge-evidence.schema.v0.1.json`)

Emitted by Native Assistant Door adapters or imported from `sourceosctl native-assistant ...` plan records.

It records:

- native bridge refs for Apple App Intents/Siri/Shortcuts, Android intents, Windows shell integrations, browser extensions, MCP, or other bridge classes;
- operation (`open-workroom`, `create-office-artifact`, `summarize`, `route-local-model`, `handoff-to-agent-machine`, `inspect-evidence`, `search-workspace`, `create-reminder`, `create-note`, `share-artifact`, or `other`);
- prompt hash-only evidence;
- user confirmation posture;
- network/model-router/agent-registry refs;
- policy posture for prompt egress, personal context reads, cross-device handoff, side effects, and raw app database access;
- side-effect flags proving whether any native assistant or app action occurred.

Native assistant bridge evidence should default to non-mutating plans. Real assistant invocation, reminder/note creation, sharing, cross-device handoff, or personal context reads must be explicit policy-gated side effects.

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
| `inputs.bundleRev` | string or null | Git commit SHA of the bundle |
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
