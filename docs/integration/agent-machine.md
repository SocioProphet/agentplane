# SourceOS Agent Machine Integration

Agent Machine is the SourceOS local workspace executor profile for Mac, Windows, and Linux operator machines. It lets AgentPlane place governed bundles onto a local Podman-backed workspace while preserving the normal AgentPlane lifecycle:

```text
Bundle -> Validate -> Place -> Run -> Evidence -> Replay
```

This integration is additive. It does not make arbitrary host shell execution an AgentPlane run.

## Contract sources

Canonical SourceOS contracts live in `SourceOS-Linux/sourceos-spec`:

- `AgentMachineLocalDataPlane`
- `AgentMachineMountPolicy`
- `TopoLVMPlacementProfile`
- `SecureHostInterfaceProfile`
- `HostInterfaceGrant`

AgentPlane references these contracts by URN/hash. It does not redefine mount policy.

## Backend intent

Bundles may declare:

```json
{
  "spec": {
    "vm": {
      "backendIntent": "agent-machine",
      "modulePath": "adapters/agent-machine"
    },
    "agentMachine": {
      "profileRef": "urn:srcos:agent-machine-profile:macos-podman-default",
      "localDataPlaneRef": "urn:srcos:agent-machine-local-data-plane:macos-default",
      "mountPolicyRef": "urn:srcos:agent-machine-mount-policy:default-deny-scoped-roots",
      "secureHostInterfaceRef": "urn:srcos:secure-host-interface:macos-default",
      "workspaceId": "urn:srcos:agent-machine-workspace:m2-demo"
    }
  }
}
```

## Evidence surface

Agent Machine runs should emit or import `AgentMachineMountEvidence`.

The artifact records:

- workspace id;
- local data-plane reference;
- mount policy reference;
- storage backend;
- path classes: `code`, `documents`, `downloads`, `cache`, `artifacts`, `media`, `app-bridge`;
- browser download hashes;
- denied mount attempts;
- optional TopoLVM node/PVC/PV metadata;
- redaction summary.

## Default local mount semantics

| Purpose | Host path | Agent path | Default posture |
|---|---|---|---|
| Code / repositories | `~/dev` | `/workspace/dev` | read/write, explicit grant |
| Generated documents / reports | `~/Documents/SourceOS/agent-output` | `/workspace/output` | read/write, explicit grant |
| Browser downloads | `~/Downloads/SourceOS/agent-downloads` | `/workspace/downloads` | browser read/write, agent read-only |

Whole-home mounts are denied. Sensitive host paths such as `.ssh`, `.gnupg`, browser profiles, keychains, cloud credential dirs, token stores, and password stores are denied by default.

## TopoLVM mode

When `storageBackend` is `topolvm-local-pv`, AgentPlane records PVC/PV and node placement metadata.

TopoLVM provides topology-aware node-local persistent volumes. It is not a cross-node shared filesystem. Cross-node sharing belongs to a higher replication or mesh storage layer.

## Implementation boundary

| Component | Responsibility |
|---|---|
| `sourceosctl` | local dry-run/apply surface for mount plans and host adapters |
| AgentPlane | validation, placement, run/evidence/replay artifacts |
| Agent Registry | non-human identity, grants, revocation |
| AgentTerm / SourceOS Shell | operator UX |
| Sociosphere | topology and repo-boundary validation |

AgentPlane should invoke `sourceosctl` or another local adapter boundary for host-local operations. It should not embed platform-specific Podman engine logic directly in bundle schemas.
