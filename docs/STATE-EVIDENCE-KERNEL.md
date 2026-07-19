# State / Projection / Observation Evidence Kernel

## Executive summary

The AgentPlane stack already distinguishes three realities, but today they are not yet elevated into one explicit reconciliation model:

1. **canonical state** — the authoritative task or backend state that can be safely mutated
2. **derived projections** — rendered or exported views that should be regenerated rather than treated as truth
3. **observed evidence** — commits, PR artifacts, verify artifacts, run bundles, and backend reads that inform interpretation but are not automatically authoritative

This dossier turns that distinction into an execution program.

## Immediate objective

Build a kernel that can:

- collect structured evidence for one task
- classify contradictions between canonical state, projections, and observations
- emit read-only explanation envelopes
- propose safe repair actions without mutating state
- promote recurring contradiction patterns into incident memory
- regression-test all of the above through signed scenario recipes

## Why now

The upstream AgentPlane architecture already gives us the correct seams:

- a canonical task container and projection model
- machine-readable explain / protocol envelopes
- a task run artifact area
- an incident collection and advice loop
- a recipes catalog model for signed scenario distribution

The missing piece is the connective tissue that lets those surfaces agree on what is true, what is stale, what is merely observed, and what is safe to do next.

## Core model

### Canonical state
Frontmatter or backend-authoritative task state. This is the only state that should be mutated by repair flows.

### Derived projection
Rendered markdown bodies, exported `tasks.json`-style views, and other caches. These should usually be refreshed, not edited.

### Observed evidence
Commits, PR artifacts, verify artifacts, run bundles, backend snapshots, incident findings, and future evidence packs.

## Initial contradiction taxonomy

### Projection drift
Canonical state is intact, but a rendered or exported view trails it.

Safe action: regenerate projection only.

### Observation gap
Work exists, but proof surfaces are sparse or delayed.

Safe action: explain and hold. Unsafe action: auto-close or auto-regress lifecycle.

### Authority conflict
Two live authorities disagree on revision, lifecycle, or lineage.

Safe action: escalate or refuse auto-repair.

### Canonical corruption
The canonical surface itself is malformed or incomplete.

Safe action: fail loudly and require operator recovery.

## Proposed artifacts in this staging branch

- `schemas/evidence-pack.schema.v0.1.json`
- `schemas/scenario-result.schema.v0.1.json`
- `schemas/reconcile-result.schema.v0.1.json`
- `patches/basilisk-labs-agentplane-state-evidence-incidents.v2.patch`
- `recipes/state-drift-lab/`
- `catalog/index-entry.state-drift-lab.v0.1.0.draft.json`

## Proposed upstream merge order

### PR-1 — incidents become evidence-aware
Add `evidence_pack` as an optional incident-registry field and teach `incidents collect` to emit a minimal evidence pack behind a flag.

### PR-2 — read-only task explanation
Add `task explain` and `task reconcile --dry-run` over the explain / protocol seam.

### PR-3 — scenario recipes and CI scorecards
Publish `state-drift-lab` through the recipes catalog and run non-blocking scenario gates in CI.

## Acceptance criteria

- no auto-repair under authority conflict
- deterministic contradiction classes
- projection refresh never mutates canonical state
- `--check` mode never writes artifacts
- scenario scorecards can be run repeatably across repositories and backends

## Constraint note

This branch is intentionally a writable staging execution surface. The live upstream Basilisk repos were re-reviewed before this work, but the connected GitHub integration is read-only there, so the actual execution path is:

1. preserve the schemas, docs, and patch materials here;
2. carry them upstream as reviewable PRs when write access exists.