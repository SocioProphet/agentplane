# Agent Action Tension Members v0

## Purpose

Defines how a single agent action declares its compression role and the tension members that stabilize it.

## Structure

Every agent action artifact in AgentPlane should carry the following tension member declarations:

```
action_id            — unique identifier for this action
compression_member   — agent | tool | service | model | repo | host
policy_ref           — policy decision ref (PolicyFabric)
identity_ref         — actor or post/authority ref
provenance_refs      — hash chain: prior action, run capsule, upstream anchors
evidence_refs        — evidence artifacts emitted by or consumed for this action
replay_ref           — replay artifact ref (required for governed runs)
revocation_path      — revocation URI; if revoked, action transitions to blocked
audit_ref            — audit trail ref (required on interventions and blocked outcomes)
```

## Tension Member Obligations by Action Type

| Action Type          | Policy | Identity | Provenance | Evidence | Replay | Revocation | Audit |
|----------------------|--------|----------|------------|----------|--------|------------|-------|
| observe              | ✓      | ✓        | ✓          | ✓        | —      | optional   | —     |
| query                | ✓      | ✓        | ✓          | ✓        | —      | optional   | —     |
| transform            | ✓      | ✓        | ✓          | ✓        | ✓      | ✓          | —     |
| write                | ✓      | ✓        | ✓          | ✓        | ✓      | ✓          | —     |
| deploy               | ✓      | ✓        | ✓          | ✓        | ✓      | ✓          | ✓     |
| revoke               | ✓      | ✓        | ✓          | ✓        | ✓      | ✓          | ✓     |
| escalate             | ✓      | ✓        | ✓          | ✓        | ✓      | ✓          | ✓     |
| trigger_execution    | ✓      | ✓        | ✓          | ✓        | ✓      | ✓          | —     |
| approval_denial      | ✓      | ✓        | ✓          | ✓        | ✓      | optional   | ✓     |

## Structural Rules

1. **`policy_ref` is always required.** No action without a PolicyFabric decision ref is structurally valid.
2. **`replay_ref` is required for actions that mutate state.** transform, write, deploy, revoke, escalate, trigger_execution, approval_denial.
3. **`audit_ref` is required for denied or blocked outcomes** and for any intervention (modified, blocked, escalated) per the bounded-action-loop contract.
4. **`revocation_path` is required for actions at R2 or above** (capability radius). See `capability-radius-v0.md`.
5. **`provenance_refs` must include at least one upstream anchor** linking this action to a run capsule, governed run, or admission artifact.

## Example

See `examples/tensegrity/agent-action-tension-members.example.json`.
