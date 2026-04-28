# SourceOS build / release bindings

This additive guide extends the existing substrate integration note by describing how `agentplane` should bind to the shared SourceOS/SociOS content/build/release object family.

## Upstream authorities

- `SociOS-Linux/SourceOS`
  - flavors
  - FCOS/coreos-assembler source material
  - Butane source material
  - installer profiles
  - release channels
  - release manifests
- `SociOS-Linux/socios`
  - Foreman/Katello lifecycle automation
  - Tekton build/customize/sign/publish pipelines
  - Argo CD placement for cluster-native automation services
- `SourceOS-Linux/sourceos-spec`
  - `ContentSpec`
  - `OverlayBundle`
  - `BuildRequest`
  - `ReleaseManifest`
  - `EnrollmentProfile`
  - `EvidenceBundle`
  - `CatalogEntry`
  - `AccessProfile`
- `SociOS-Linux/workstation-contracts`
  - local runner↔adapter subprocess IPC
- `SocioProphet/TriTRPC`
  - canonical deterministic remote/authenticated transport

## Role of agentplane

`agentplane` stays the execution control plane.
It should not become the authority for substrate content or release definitions.

For SourceOS/SociOS build and publication lanes, `agentplane` should:
- accept or reference a `BuildRequest`
- preserve refs to `ContentSpec`, `OverlayBundle`, and `EnrollmentProfile`
- preserve refs to `ReleaseManifest` and `EvidenceBundle`
- emit execution evidence without redefining those objects

## Binding posture

The first step is an additive bundle fragment that allows implementations to attach refs such as:
- `contentSpecRef`
- `overlayRefs`
- `buildRequestRef`
- `releaseManifestRef`
- `enrollmentProfileRef`
- `evidenceBundleRef`
- `localExecutionProtocolRef`
- `remoteExecutionProtocolRef`

This guide does not yet modify the canonical bundle schema in place.

## Follow-on

1. project the binding refs into Validation / Placement / Run / Replay artifacts
2. extend validation to recognize the binding fragment once the field placement is accepted
3. bind local execution to the M2 IPC pack
4. bind remote execution and cross-host transport to TriTRPC-native lanes where appropriate
