# QEMU Local Evidence Wrapper Reconciliation — 2026-05-25

Issue: `SocioProphet/agentplane#168`

Open PR audited:

```text
SocioProphet/agentplane#221
```

## Finding

The PR payload is already present on current `main`:

```text
runners/qemu-local-evidence.sh
```

The wrapper is additive and evidence-aware. It delegates to `runners/qemu-local.sh` and only emits postcondition/divergence evidence when the relevant environment inputs are present.

## Current replay action

This reconciliation PR adds the missing focused validation surface:

```text
.github/workflows/qemu-local-evidence.yml
```

The workflow syntax-checks the wrapper and compiles the evidence emitter.

## Boundary

This replay adds validation coverage only.

It does not run QEMU, execute bundles, invoke providers, contact a network, mutate a workspace, or emit live execution evidence.
