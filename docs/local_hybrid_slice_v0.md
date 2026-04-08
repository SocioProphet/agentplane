# Local-Hybrid Slice v0

## Purpose

This document freezes the first end-to-end execution slice for Agentplane.

The slice is intentionally narrow. It exists to prove the architecture, not to implement every capability class at once.

## Scope

The first slice is:

- a local-first request enters the device-local supervisor
- local retrieval and local task planning run first
- policy decides whether any remote execution is permitted
- Agentplane resolves a remote capability when policy allows it
- a tenant worker executes the bound capability
- evidence is appended
- a replay/cairn handle is materialized

## Seven-method lifecycle

1. `supervisor.v1.Session/Open`
2. `supervisor.v1.Task/Plan`
3. `policy.v1.Decision/Evaluate`
4. `control.v1.Capability/Resolve`
5. `worker.v1.Capability/Execute`
6. `evidence.v1.Event/Append`
7. `replay.v1.Cairn/Materialize`

Agentplane owns the tenant-side responsibilities for steps 4 and 5 directly, and may mirror or participate in 3 and 6 where tenant policy and evidence relays are required.

## What Agentplane already has

The repo already contains artifact schema scaffolds for:

- session artifacts
- promotion artifacts
- reversal artifacts
- bundle spec patch fields for runtime behavior

These are useful because they establish the repo as a runtime artifact plane rather than only a conceptual architecture bucket.

## What Agentplane must add next

### Gateway

The gateway is the tenant ingress for remote-eligible work. It should:

- accept already-classified and policy-scoped work from the local supervisor
- validate capability binding requests
- reject out-of-policy egress or side-effect requests
- emit tenant-side evidence handoff events

### Capability registry

The capability registry maps a logical capability ID to an execution binding. A binding should minimally describe:

- capability instance ID
- worker endpoint
- supported execution lanes
- timeout and context limits
- side-effect posture
- required credentials or scopes

### Worker runtime

The worker runtime wraps the remote execution contract. It should:

- execute only typed capability payloads
- run with scoped credentials
- record input and output digests
- emit provenance metadata suitable for evidence append

## Relation to existing schemas

The existing artifact schemas are not wasted work. They align with the future execution lifecycle as follows:

- `session-artifact.schema.v0.1.json` supports session-level receipts and replay references
- `promotion-artifact.schema.v0.1.json` supports later promotion/review flows for side-effecting actions
- `reversal-artifact.schema.v0.1.json` supports rollback/reversal for promoted changes
- `bundle.schema.patch.json` already introduces runtime-oriented fields such as `sessionPolicyRef`, `skillRefs`, `memoryNamespace`, `worktreeStrategy`, `rolloutFlags`, `telemetrySink`, and `receiptSchemaVersion`

## Non-goals for v0

- generalized autonomous multi-agent swarms
- unconstrained public-provider model egress
- long-lived secret material inside workers
- untyped prompt-only worker contracts
- cloud-first session authority

## Immediate follow-on work

1. Add gateway scaffolding.
2. Add capability-registry scaffolding.
3. Add worker-runtime scaffolding.
4. Add examples that bind a single capability such as `summarize.abstractive.v1`.
5. Align shared schemas and fixtures with `TriTRPC` and `socioprophet-standards-storage`.
