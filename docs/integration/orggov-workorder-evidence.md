# OrgGov Work Order Evidence Binding v0.1

## Purpose

This binding connects Organization Governance Control Plane work orders to AgentPlane evidence artifacts.

The OrgGov product loop is:

```text
Objective → Workroom → Actor → Role → Policy → Asset → Action → Evidence → Review → Outcome → Score → Learning
```

AgentPlane owns the execution and evidence part of that loop. It does not own the product UI, policy authority, actor registry, or scorecard semantics.

## Contract files

- `schemas/orggov-workorder-evidence.v0.1.schema.json`
- `examples/orggov/orggov-workorder-evidence.v0.1.example.json`
- `tools/validate_orggov_workorder_evidence.py`

## Binding fields

The v0 binding carries:

- `workroomRef`
- `workOrderRef`
- `actorRef`
- `roleBindingRef`
- `policyDecisionRefs`
- `bundleRef`
- `validationArtifactRef`
- `placementDecisionRef`
- `runArtifactRef`
- `replayArtifactRef`
- `sessionArtifactRef`
- `outputRefs`
- `reviewRefs`
- `outcomeRefs`
- `reversalRefs`

## Invariants

- Every work-order evidence binding must include a workroom and work order.
- Every binding must include actor, role binding, and policy decision references.
- Validation, placement, run, replay, and session references are explicit.
- Output references point to artifacts, not raw private prompts or credentials.
- Replay posture remains visible even when the binding is a fixture.

## Cross-repo links

- Parent: `SocioProphet/prophet-platform#406`
- AgentPlane workstream: `SocioProphet/agentplane#104`
- Policy gates: `SocioProphet/policy-fabric#57`
- Actor authority: `SocioProphet/agent-registry#18`
- Workspace control room: `SocioProphet/prophet-workspace#15`
