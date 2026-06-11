# Authority-Dependency Evidence Contract

This document defines the `AuthorityDependencyEvidence` contract owned by Agentplane.

## Purpose

`AuthorityDependencyEvidence` records that a runtime actor depended on a specific authority or trust surface during an admitted execution — and whether that authority was consumed, denied, blocked, or otherwise constrained.

It is evidence-only: Agentplane records the outcome of an authority dependency lookup. It does not own the authority definition, the trust surface topology, or the policy decision.

## Canonical loop position

```text
Act -> [authority dependency resolved] -> AuthorityDependencyEvidence emitted -> Receipt -> Learn
```

Emitted after execution or at the point of blocking, before receipt finalization.

## Required fields

| Field | Description |
|---|---|
| `evidence_id` | Stable identifier for this evidence record |
| `run_id` | The run that produced this dependency |
| `actor_ref` | The actor that consumed (or was denied) the authority |
| `authority_dependency_id` | Identifier of the declared authority dependency |
| `trust_surface_ref` | Trust surface consulted |
| `policy_decision_ref` | Policy decision that governed the outcome |
| `control_effect` | Named control effect applied |
| `target_ref` | Resource or endpoint targeted |
| `evidence_outcome` | One of `used`, `denied`, `blocked`, `cancelled`, `quarantined`, `degraded`, `simulated`, `not_used` |
| `recorded_at` | ISO-8601 timestamp |

## Outcome semantics

| Outcome | Meaning |
|---|---|
| `used` | Authority was available and consumed |
| `denied` | Policy explicitly denied the dependency |
| `blocked` | Control surface blocked before policy evaluation |
| `cancelled` | Dependency was declared but action was cancelled |
| `quarantined` | Actor placed under quarantine; dependency not resolved |
| `degraded` | Authority available in degraded mode only |
| `simulated` | Dry-run or simulation; no real side effects |
| `not_used` | Dependency declared but not consumed in this run |

## Boundary rules

- Agentplane owns emission and replay of evidence records.
- Agentplane does not own the trust surface topology (ProCybernetica, Superconscious).
- Agentplane does not own the policy decision (Policy Fabric).
- Agentplane does not mutate network/runtime/model/host state.
- Hash-only for sensitive fields; never inline credentials.

## Schema

`schemas/authority-dependency-evidence.schema.v0.1.json`

## Examples

- `examples/authority-dependency-evidence/valid.authority-dependency-evidence.example.json` — outcome `used`
- `examples/authority-dependency-evidence/blocked.authority-dependency-evidence.example.json` — outcome `blocked`

## Cross-references

- SocioSphere boundary atlas: consumes evidence records for audit
- Policy Fabric: provides `policy_decision_ref` referenced here
- ProCybernetica #49: trust surface definitions
- Superconscious #10: trust surface topologies
