# agentplane

Agentplane is the tenant-side control and execution plane for local-first and hybrid agents.

This repository is not the local supervisor and it is not the canonical wire-spec repository. Instead, it is the remote control-plane and worker-plane complement to the device-local runtime.

## What already exists here

The current repository already contains useful runtime artifact scaffolds and local-state conventions:

- `schemas/session-artifact.schema.v0.1.json`
- `schemas/promotion-artifact.schema.v0.1.json`
- `schemas/reversal-artifact.schema.v0.1.json`
- `schemas/bundle.schema.patch.json`
- `state/pointers/.keep`
- `.gitignore` rules for local `artifacts/` and machine-local pointer state

Those files tell us two important things:

1. Agentplane already assumes evidence-bearing runtime artifacts.
2. Agentplane already assumes machine-local pointer state should not be committed.

## Repository role

Agentplane owns the **tenant-side** parts of the first local-hybrid slice:

- gateway and ingress policy handoff for remote-eligible tasks
- capability resolution from logical capability ID to worker binding
- worker runtime envelopes for remote execution
- promotion and reversal semantics for future side-effecting flows
- tenant-side evidence handoff hooks

Agentplane does **not** own:

- the local supervisor runtime (`sociosphere`)
- the canonical deterministic transport and fixtures (`TriTRPC`)
- the shared cross-repo contract canon (`socioprophet-standards-storage`)

## Planned layout

- `docs/` — architecture notes, slice definitions, repo map
- `gateway/` — tenant ingress and policy-gated dispatch adapters
- `capability-registry/` — logical capability descriptors and bindings
- `worker-runtime/` — tenant execution wrappers and runtime contracts
- `schemas/` — artifact schemas and patch fragments used by runtime flows

## Current implementation stance

The first slice is deliberately narrow:

- local-first planning and retrieval
- optional tenant execution only after policy approval
- typed capability resolution
- evidence append and replay/cairn materialization
- no public-provider egress by default
- no generic multi-agent prompt soup

See `docs/local_hybrid_slice_v0.md` for the execution slice and `docs/repository_map.md` for cross-repo boundaries.
