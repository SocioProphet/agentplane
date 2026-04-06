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
