# Prophet Understand Dispatch

## Purpose

AgentPlane consumes Prophet Understand / Repo Intelligence v0 artifacts to make agent work orders graph-aware, bounded, and evidence-preserving.

Repo graph context informs scope. It does not grant mutation authority.

## Input artifact

Canonical artifact:

```text
.prophet/prophet-understanding.json
```

Normative platform contract:

```text
SocioProphet/prophet-platform/schemas/repo-intelligence/prophet-understanding.schema.json
```

## RepoGraphContext

A graph-aware work order should be able to carry:

- repo full name
- commit or ref
- artifact path
- artifact hash
- schema version
- changed paths
- affected node IDs
- affected edge IDs
- affected test node IDs
- affected doc node IDs
- affected policy node IDs
- source anchors
- provenance receipt IDs
- policy status
- validation status

## Work order use cases

- code fix with affected graph scope
- documentation update tied to affected docs and contracts
- policy review tied to affected policy nodes
- PR impact review tied to changed paths and graph edges
- test repair tied to test nodes and covered contract/service nodes

## Required agent output

Agent output must include:

- affected node IDs when available
- affected edge IDs when available
- source anchors for factual claims
- provenance receipt IDs for graph-derived facts
- validation command output or explicit not-run status
- policy status and review requirement
- non-goals preserved

## Missing/stale graph behavior

If the graph artifact is missing, stale, invalid, or low-confidence, the work order must carry that status explicitly. Agents may still perform bounded analysis, but must not claim graph-backed certainty.

## Non-goals

- AgentPlane does not own graph generation.
- AgentPlane does not bypass Policy Fabric.
- Inferred graph facts cannot become mutation authority.
- Graph scope does not relax branch protection, review policy, or execution leases.
