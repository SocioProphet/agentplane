# DurableGraph runtime skeleton

This directory seeds a clean-room durable graph runtime contract for `agentplane`.

## Why this exists

We want the execution semantics we studied from external durable graph runtimes:

- graph template upsert + validation
- graph trigger -> run/session creation
- graph-scoped store
- explicit signal handling (`prune`, `requeue_after`)
- runtime worker registration and long-lived polling

But we do **not** want to take a non-permissive runtime dependency into the core `agentplane` path.

This package therefore defines an internal protocol and compiler shape that `agentplane` can own directly.

## Design rules

- Standards canon remains external to this package and is imported via `policy/imports/control-matrix/manifest.json`.
- Runtime compilation must fail closed when required compiled control bundles are absent.
- Graph/session lifecycle events are distinct from terminal run artifacts.
- Signals are not failures and must not be coerced into `RunArtifact.status = failure`.
- Any compatibility work for external runtimes belongs in an experiments lane, not the mainline.

## MVP graph

The first compiled graph shape is intentionally narrow:

1. `APControlGateNode`
2. `APExecNode`
3. `APEvidenceNode`

The root node receives run-scoped trigger inputs and store values. Terminal evidence is written back into the bundle artifact directory.
