# Run/Replay Artifacts Reconciliation — 2026-05-23

Issue: `SocioProphet/agentplane#168`

Source branch audited:

```text
codex/run-replay-artifacts-v0-1
```

## Finding

The stale branch payload is already present on current `main`:

```text
docs/sociosphere-bridge.md
schemas/replay-artifact.schema.v0.1.json
schemas/run-artifact.schema.v0.1.json
scripts/emit_replay_artifact.py
scripts/emit_run_artifact.py
```

The mainline version is richer than the stale branch because the schemas and emitters also carry governance-context and SourceOS binding fields.

## Current replay action

This reconciliation PR adds the missing focused validation surface:

```text
.github/workflows/run-replay-artifacts.yml
examples/run-replay/minimal-bundle.json
```

The workflow validates the schemas, compiles both emitters, emits synthetic run/replay artifacts into `/tmp`, and JSON-validates the outputs.

## Boundary

This replay adds validation coverage only.

It does not execute a bundle, invoke a provider, touch a network, mutate a repository, or perform external writes.
