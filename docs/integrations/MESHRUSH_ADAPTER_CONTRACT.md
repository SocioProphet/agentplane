# MeshRush Adapter Contract for Agentplane

Status: v0 integration contract

## Purpose

This document defines how a MeshRush crystallized graph artifact becomes an Agentplane execution candidate without bypassing governance.

MeshRush owns graph operation: entry, diffusion, grounding, stop conditions, crystallization, and evidence traces.

Agentplane owns governed execution: validate, run, evidence, replay, rollout, approval state, and execution policy.

## Core rule

MeshRush may recommend actions. Agentplane decides whether an action can execute.

```text
MeshRush crystallized graph artifact
  -> Agentplane execution candidate
  -> validation
  -> approval gate when required
  -> run only if approved and policy permits
  -> evidence and replay record
```

## Input artifact

Required MeshRush fields:

- `artifact_id`
- `graph_view_id`
- `entry_node_refs`
- `traversed_node_refs`
- `crystallized_claims`
- `policy_refs`
- `recommended_next_action`
- `provenance`
- `classification`

## Agentplane candidate mapping

| MeshRush field | Agentplane candidate field |
| --- | --- |
| `artifact_id` | `source_artifact_ref` |
| `graph_view_id` | `context_ref` |
| `entry_node_refs` | `entry_refs` |
| `traversed_node_refs` | `evidence_refs` |
| `crystallized_claims` | `claims` |
| `policy_refs` | `policy_refs` |
| `recommended_next_action.action_type` | `requested_action_type` |
| `recommended_next_action.action_boundary` | `approval_boundary` |
| `provenance.source_refs` | `source_refs` |
| `classification.handling_tags` | `handling_tags` |

## Approval boundaries

Allowed boundaries:

- `advisory`: no execution; record/recommend only.
- `approval_required`: execution candidate may be created but cannot run without approval.
- `executable`: may execute if policy validation passes.
- `blocked`: must not create runnable execution.

Default boundary is `approval_required` when missing or ambiguous.

## Candidate object shape

A v0 Agentplane candidate should contain:

- candidate ID;
- source artifact ref;
- requested action type;
- approval boundary;
- policy refs;
- evidence refs;
- claims;
- classification/handling tags;
- validation status;
- approval state;
- replay requirements;
- rollback semantics.

## Validation requirements

Agentplane must validate:

1. The MeshRush artifact is structurally valid.
2. Policy refs are present.
3. Evidence refs are non-empty.
4. The approval boundary is recognized.
5. The requested action type is allowed by policy.
6. The artifact does not request direct mutation of GAIA/OFIF/Lattice records.
7. Classification and handling tags are preserved.

## Non-goals

- MeshRush does not execute actions.
- Agentplane does not reinterpret MeshRush claims as facts without evidence.
- Agentplane does not bypass SocioSphere governance gates for fleet or workspace policies.
- Advisory recommendations must not mutate external systems.

## First fixture path

The first integration fixture should map:

`SocioProphet/meshrush:fixtures/graph-views/soil-intelligence-crystallization.sample.v1.json`

into an approval-aware Agentplane candidate.

Because the fixture action boundary is `advisory`, the first candidate must be non-runnable and evidence-record-only.
