# Agentplane

Agentplane is an execution control plane for governed bundle runs.

The public contract is deliberately simple and evidence-forward:

1. **Bundle** — the deployment unit in `bundles/`.
2. **Validate** — `scripts/validate_bundle.py` enforces the minimum contract and compliance gates.
3. **Place** — `scripts/select-executor.py` selects an executor and emits a `PlacementDecision`.
4. **Run** — a runner backend executes the bundle and emits a `RunArtifact`.
5. **Replay** — `scripts/emit_replay_artifact.py` records the minimum replay inputs.
6. **Lifecycle** — promotion, reversal, and session artifacts extend the execution story.

## Repository map

- `bundles/` — example deployment bundles.
- `docs/system-space.md` — system-space strategy and execution model.
- `docs/sociosphere-bridge.md` — seam between `sociosphere` and `agentplane`.
- `docs/runtime-governance/control-matrix-integration.md` — governance/control-loop integration plan.
- `docs/replay-boundary.md` — replay scope, non-goals, and side-effect rules.
- `examples/receipts/` — receipt-oriented examples and trace assembly reference.
- `schemas/` — JSON Schemas for Bundle, RunArtifact, ReplayArtifact, PromotionArtifact, ReversalArtifact, SessionArtifact, plus the missing ValidationArtifact and PlacementDecision contracts added in this patch.
- `scripts/` — validation, placement, artifact emission, demo, and hygiene tooling.
- `runners/` — backend contract surface.

## Evidence surface

Agentplane already treats execution as evidence-producing work. The current public evidence types are:

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact`
- `ReplayArtifact`
- `PromotionArtifact`
- `ReversalArtifact`
- `SessionArtifact`

The repo also carries receipt-oriented examples under `examples/receipts/` and runtime-governance planning under `docs/runtime-governance/`.

## Current positioning

Publicly, Agentplane is best described as **workflow orchestration / execution control** rather than an agent gateway.

The repo is centered on bundle validation, executor selection, run artifacts, replay inputs, lifecycle artifacts, and governance-linked evidence. That is why the current external listing recommendation is **Workflow Orchestration**.

## Known contract gap still worth closing

Two concepts are already present in behavior and docs but were not yet first-class public schema files on `main` when this patch was prepared:

- `ValidationArtifact`
- `PlacementDecision`

This patch adds schemas for both and adds a concise replay-boundary document so the repo root is no longer just a file tree plus About text.
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
