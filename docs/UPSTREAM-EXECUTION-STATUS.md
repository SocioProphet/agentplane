# Upstream execution status

Re-reviewed: 2026-04-07

## Upstream repositories inspected

- `basilisk-labs/agentplane`
- `basilisk-labs/agentplane-recipes`
- `basilisk-labs/codex-swarm`
- `basilisk-labs/openclaw-deus`

## Connector permissions observed

### Readable but not writable

The connected GitHub integration exposes `pull: true` and `push: false` on the Basilisk Labs upstream repositories listed above.

### Writable staging surface

`SocioProphet/agentplane` is writable from the connected integration and already contains AgentPlane-related artifact scaffolds. This branch therefore stages:

- proposal schemas
- upstream patch materials
- recipe bundle text surfaces
- catalog draft entry
- execution notes and merge order

## What has been executed here

- feature branch created from current `main`
- execution dossier added
- state-evidence schemas staged
- recipe/catalog draft assets staged
- upstream incidents patch staged
- pull request to `main` will be opened from this branch

## What has not yet been executed upstream

Because the upstream Basilisk repositories are read-only from this integration, the following actions remain intentionally unperformed there:

- applying the incidents evidence-pack patch directly to `basilisk-labs/agentplane`
- publishing `state-drift-lab` into `basilisk-labs/agentplane-recipes`
- wiring CI scorecards upstream

## Recommended upstream port order

1. apply the incidents patch to `basilisk-labs/agentplane`
2. add read-only `task explain` and `task reconcile --dry-run`
3. publish `state-drift-lab` to the recipes catalog
4. add scenario scorecards to CI

## Preservation principle

This branch exists to avoid losing work while upstream write access is unavailable. It is a staging execution surface, not a claim that upstream has already merged these changes.