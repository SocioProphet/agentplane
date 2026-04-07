# SocioProphet AgentPlane staging

This repository is being used as a writable staging surface for AgentPlane schema and integration artifacts.

## Current focus

This branch stages the **State / Projection / Observation Evidence Kernel** work:

- evidence-pack schema scaffolds
- reconcile-result and scenario-result proposal schemas
- an upstream execution dossier for `basilisk-labs/agentplane`
- a draft recipe/catalog surface for `state-drift-lab`
- an upstream-ready incidents patch bundle

## Why this repo is the staging surface

The live upstream repos reviewed for this work are currently readable from the connected GitHub integration but not writable:

- `basilisk-labs/agentplane`
- `basilisk-labs/agentplane-recipes`
- `basilisk-labs/codex-swarm`
- `basilisk-labs/openclaw-deus`

By contrast, `SocioProphet/agentplane` is writable and already contains AgentPlane-related schema scaffolds, so it is the correct place to preserve the execution pack, schemas, and PR-ready upstream patch materials without losing work.

## Branch contents

See:

- `docs/STATE-EVIDENCE-KERNEL.md`
- `docs/UPSTREAM-EXECUTION-STATUS.md`
- `schemas/`
- `patches/`
- `recipes/state-drift-lab/`
- `catalog/`

## Intended next move

Once upstream write access exists, the materials in this repo should be ported or applied to the upstream AgentPlane and recipes repos as small, reviewable pull requests.