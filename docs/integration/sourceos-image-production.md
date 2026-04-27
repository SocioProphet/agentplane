# SourceOS Image Production Integration Lane

Status: draft
Owner: Agentplane
Consumes:
- SociOS-Linux/SourceOS: `docs/ARTIFACT_TRUTH.md`
- SociOS-Linux/socios: `docs/FCOS_FOREMAN_KATELLO_SUBSTRATE.md`
- SociOS-Linux/socios: `foreman/KATELLO_CONTENT_MODEL.md`
- SociOS-Linux/socios: `pipelines/tekton/pipeline-customize-live-iso.yaml`
- SociOS-Linux/socios: `pipelines/tekton/task-customize-live-iso.yaml`
- SociOS-Linux/socios: `pipelines/tekton/task-publish-katello-file-repo.yaml`
- SociOS-Linux/socios: `pipelines/tekton/task-smoke-live-iso.yaml`
- SourceOS-Linux/sourceos-spec: shared typed contracts and URN discipline
- SocioProphet/prophet-platform: `docs/CONTAINER_BUILD_SUBSTRATE.md`
- SocioProphet/prophet-platform: `docs/SOURCEOS_M2_LIFECYCLE_PROOF.md`
- SocioProphet/sociosphere: `governance/SOURCEOS_SUBSTRATE_BOUNDARIES.yaml`

## Purpose

Agentplane is the governed execution control plane for bundle runs. SourceOS image production should enter Agentplane only as a governed bundle lane:

```text
Bundle -> Validate -> Place -> Run -> Evidence -> Replay
```

Agentplane does not own SourceOS artifact truth, Foreman/Katello automation, or shared schema canon. It wraps those authorities with validation, executor placement, run artifacts, replay inputs, and promotion/reversal evidence.

## Authority split

| Concern | Owner | Agentplane behavior |
|---|---|---|
| Flavors, cosa/build-source material, Butane/Ignition, installer profiles, channels, manifests | `SociOS-Linux/SourceOS` | consume as artifact-truth inputs |
| Foreman/Katello hosts, Smart Proxy, Tekton build/customize/sign/publish/promote, Argo CD, enrollment/rollout/promotion automation | `SociOS-Linux/socios` | execute or delegate through controlled bundles |
| Shared schemas/contracts | `SourceOS-Linux/sourceos-spec` | validate payloads and URNs where applicable |
| Product/control-plane proof and M2 lifecycle demo | `SocioProphet/prophet-platform` | consume proof outputs and evidence refs |
| Governance boundary source map | `SocioProphet/sociosphere` | enforce source-of-truth boundaries |
| Execution evidence/replay | `SocioProphet/agentplane` | own Validation/Placement/Run/Replay artifacts |

## Bundle lane: sourceos-image-production

A SourceOS image-production bundle should declare:

```yaml
metadata:
  name: sourceos-image-production-...
  source:
    git:
      rev: ...
  licensePolicy:
    allowAGPL: false
spec:
  policy:
    lane: staging | prod
    humanGateRequired: true
    maxRunSeconds: ...
  sourceos:
    artifactTruthRef: SociOS-Linux/SourceOS path or commit
    flavorRef: flavors/...
    installerProfileRef: installer/...
    channelRef: channels/...
    manifestRef: manifests/...
  sociosAutomation:
    substrateDocRef: docs/FCOS_FOREMAN_KATELLO_SUBSTRATE.md
    katelloContentModelRef: foreman/KATELLO_CONTENT_MODEL.md
    tektonPipelineRef: pipelines/tekton/pipeline-customize-live-iso.yaml
    katelloProduct: SourceOS ...
    katelloRepository: ...
    katelloLifecycleEnvironment: dev | qa | prod | site
  outputs:
    releaseSetRef: optional Prophet Platform ReleaseSet reference
    bootReleaseSetRef: optional Prophet Platform BootReleaseSet reference
    evidenceBundleRef: optional EvidenceBundle reference
```

The current `schemas/bundle.schema.v0.1.json` does not yet make `spec.sourceos` and `spec.sociosAutomation` first-class. Until that schema is extended, bundle authors should place these fields under a governed extension block or a typed sidecar file and reference it from `spec.policy.policyPackRef` or bundle metadata.

## Execution model

Agentplane should execute this lane as one of two patterns:

### Pattern A: delegate to `socios` automation

Use Agentplane to validate, place, invoke, and record the execution of an existing `socios` Tekton/Foreman/Katello lane.

```text
validate SourceOS bundle
-> place runner with access to Tekton/Katello credentials via secret refs
-> invoke socios pipeline-customize-live-iso
-> capture Tekton run refs, Katello content refs, ISO path/digest, smoke receipt
-> emit RunArtifact and ReplayArtifact
```

### Pattern B: local deterministic proof wrapper

Use Agentplane to run or validate local deterministic proofs, such as Prophet Platform's M2 lifecycle proof bundle, without host mutation.

```text
validate proof bundle
-> place local executor
-> run deterministic proof generator or smoke test
-> capture generated objects and digests
-> emit RunArtifact and ReplayArtifact
```

## Evidence requirements

Every SourceOS image-production bundle must emit or reference:

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact`
- `ReplayArtifact`
- SourceOS artifact-truth refs
- `socios` automation refs
- Katello Product / Repository / Content View / Lifecycle Environment refs where applicable
- image digest, ISO digest, OSTree ref, or Katello content ref
- smoke receipt for live ISO lanes
- ReleaseSet / BootReleaseSet refs where applicable
- rollback or previous-known-good ref

## Replay boundary

Replay must record enough to re-run or audit the image-production lane without pretending to recreate external mutable systems automatically.

Replay records should include:

- exact Git commit refs for `SourceOS`, `socios`, `sourceos-spec`, and invoking repo;
- Tekton PipelineRun/TaskRun refs where applicable;
- Katello content references or upload receipts;
- secret references only, never inline secrets;
- artifact digests;
- policy pack hash;
- executor placement decision.

## Blocking conditions

Agentplane must fail closed when:

- artifact truth is missing;
- `socios` automation path is missing for Foreman/Katello lanes;
- Katello product/repository/lifecycle environment is missing for publish lanes;
- output digest or content ref is missing;
- smoke check is required but absent;
- secrets are inline instead of references;
- AGPL is allowed;
- policy gate has no exact row match;
- human gate is required and not satisfied;
- runtime or replay evidence cannot be emitted.

## Near-term schema gap

The next schema patch should add an optional `spec.sourceos` object and `spec.sociosAutomation` object to `schemas/bundle.schema.v0.1.json` or introduce an additive patch schema. Until then, this document defines the integration lane and the evidence requirements.
