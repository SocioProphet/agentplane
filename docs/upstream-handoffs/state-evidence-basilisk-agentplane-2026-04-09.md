# State / Projection / Evidence kernel handoff for Basilisk Labs AgentPlane

Date: 2026-04-09
Author: ChatGPT session handoff

## Purpose

This document captures a prepared patch ladder for the public `basilisk-labs/agentplane` and `basilisk-labs/agentplane-recipes` repositories.

The GitHub connector available in this session has **read access** to `basilisk-labs/*` but **does not have write scope** there. It **does** have write scope to `SocioProphet/agentplane`, so this handoff is being stored here to preserve the work in GitHub rather than leaving it only in ephemeral sandbox artifacts.

## Verified public upstream heads

### basilisk-labs/agentplane
- branch: `main`
- verified head: `1bb989422caa8c476fed0c8c693b1191bee1d655`
- visible title: `workflow: reconcile stale shipped task state (#164)`

### basilisk-labs/agentplane-recipes
- branch: `main`
- verified head: `021c99bc8527220bf9339872903cf30105adea97`
- visible title: `Remove legacy requires_human_approval from Dokploy recipe`

## Goal

Add a first-class State / Projection / Evidence kernel to AgentPlane so the control plane can:
- distinguish canonical task state from generated/exported projections
- collect structured evidence packs
- explain contradictions before mutating anything
- emit dry-run reconcile plans
- block unsafe repair under backend authority or sync conflict
- ship a recipe-backed drift/failure corpus (`state-drift-lab`)

## Patch ladder prepared

### AgentPlane
1. **v2 incidents evidence-pack plumbing**
   - add `evidence_pack` to incident entries
   - add `--evidence-pack` to `agentplane incidents collect`
   - write `evidence-pack.v1.json`

2. **PR2 incidents tests**
   - parse / format / roundtrip coverage for `evidence_pack`

3. **PR1 task explain**
   - read-only task-state explanation surface

4. **PR1 task reconcile + focused CI**
   - dry-run repair planning
   - focused state-evidence workflow

5. **PR2 evidence expansion**
   - best-effort PR / verify / backend projection evidence
   - contradiction fingerprints

6. **PR3 backend authority conflicts**
   - distinguish refreshable drift from canonical backend disagreement

7. **PR4 backend snapshot + sync conflicts**
   - ingest explicit backend task snapshot
   - classify cache-vs-backend sync conflict

8. **PR5 backend warning metadata**
   - ingest backend list warnings / revision-guard warning signals
   - block unsafe repair when backend warning smoke exists

### AgentPlane Recipes
9. **PR1 state-drift-lab recipe**
   - scenario corpus for drift / contradiction cases

10. **PR2 recipe integrity workflow**
   - verify release tarball + sha256 + catalog entry consistency

## Intended PR split

### Repo: `basilisk-labs/agentplane`
- PR A: incidents evidence-pack plumbing + tests
- PR B: `task explain` + `task reconcile` + focused CI
- PR C: backend authority / snapshot / warning conflict ladder

### Repo: `basilisk-labs/agentplane-recipes`
- PR D: `state-drift-lab`
- PR E: integrity workflow for recipe release assets

## Key design decisions

1. **Do not create a shadow canonical task file.**
   Canonical task state remains the task container / frontmatter model in the upstream repo. The kernel adds evidence and explanation surfaces around that truth model.

2. **Explain before repair.**
   `task explain` is read-only. `task reconcile` is dry-run only in the current ladder.

3. **Separate drift from authority conflict.**
   Refreshable projection/cache drift must not be treated like a canonical backend disagreement.

4. **Treat backend warnings as blocking evidence.**
   Warning metadata and revision-guard smoke should stop unsafe repairs.

5. **Keep recipes as the failure museum.**
   Contradiction logic belongs in AgentPlane core; packaged drift scenarios belong in `agentplane-recipes`.

## Current operational status

The patch ladder has been prepared and validated incrementally with `git apply --check` against reconstructed upstream snapshots, but **has not been applied to the live Basilisk Labs repositories from this session** because the connector installation does not allow branch creation or writes there.

## What must happen next

1. Install / enable GitHub write scope for:
   - `basilisk-labs/agentplane`
   - `basilisk-labs/agentplane-recipes`

2. Apply the prepared patch ladder in dependency order.

3. Run the focused test lane on live branches.

4. Open PRs in the split listed above.

## Minimal live smoke checks after apply

```bash
bun x vitest run \
  packages/agentplane/src/runtime/incidents/resolve.test.ts \
  packages/agentplane/src/commands/task/explain.unit.test.ts \
  packages/agentplane/src/commands/task/reconcile.unit.test.ts

bun run agentplane incidents collect <task-id> --evidence-pack --json
bun run agentplane task explain <task-id>
bun run agentplane task reconcile <task-id>
```

## Why this handoff exists here

This file is a deliberate preservation step so the work is recorded in a write-capable GitHub repository even when the target upstream repositories are outside the connector’s write scope.
