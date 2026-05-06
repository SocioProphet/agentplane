# Superconscious ReasoningRun Integration

Superconscious is the reference governed cognition loop. AgentPlane remains the execution, evidence, placement, and replay authority.

This integration maps SourceOS reasoning contracts into AgentPlane evidence and replay surfaces without requiring AgentPlane to become the cognition loop.

## Inputs

Superconscious M1 emits compatibility artifacts:

```text
events.jsonl
reasoning-run.json
agentplane-evidence.json
replay-plan.json
benchmark-result.json
```

It also emits SourceOS canonical artifacts:

```text
reasoning-events.sourceos.jsonl
reasoning-run.sourceos.json
reasoning-receipt.json
reasoning-replay-plan.json
reasoning-benchmark.json
```

AgentPlane should prefer the canonical SourceOS artifacts and keep compatibility support during M1/M2.

## Canonical SourceOS contracts

Owned by `SourceOS-Linux/sourceos-spec`:

| Contract | Purpose |
|---|---|
| `ReasoningRun` | Top-level governed reasoning run record. |
| `ReasoningEvent` | Safe operational trace event. |
| `ReasoningReceipt` | Final reasoning receipt with trace hash, coordination posture, and replay class. |
| `ReasoningReplayPlan` | Replay class, inputs, and constraints. |
| `ReasoningBenchmark` | Evidence-backed benchmark result. |

## AgentPlane mapping

| Superconscious artifact | AgentPlane concept | Notes |
|---|---|---|
| `reasoning-run.sourceos.json` | Session / run context | Read task, agent, workspace, safe trace posture, event refs. |
| `reasoning-events.sourceos.jsonl` | Event stream input | Safe operational trace only; no raw private reasoning required. |
| `reasoning-receipt.json` | Evidence receipt | Maps to evidence lifecycle and receipt registry. |
| `reasoning-replay-plan.json` | ReplayArtifact input | Preserve replay class and input/constraint refs. |
| `reasoning-benchmark.json` | Gate / benchmark result | Should be required before promotion. |

## Required invariants

- `ReasoningRun.safeTrace.rawPrivateReasoning` must be `not-collected`.
- `ReasoningRun.safeTrace.mode` must be `operational-trace-only`.
- `ReasoningReceipt.runRef` must match the `ReasoningRun.id`.
- `ReasoningReplayPlan.runRef` must match the `ReasoningRun.id`.
- `ReasoningBenchmark.runRef` must match the `ReasoningRun.id`.
- `ReasoningBenchmark.passed` must be true for promotion.
- Replay class must be one of `exact`, `best-effort`, `evidence-only`, or `non-replayable-side-effect`.

## M1 fixture target

The first AgentPlane fixture validates a Superconscious deterministic run directory with no network, no model call, no host mutation, and memory proposal-only posture.

Validation proves:

```text
ReasoningRun -> ReasoningReceipt -> ReasoningReplayPlan -> ReasoningBenchmark
```

are internally consistent.

## Current validator

```bash
python3 scripts/import_superconscious_reasoning.py examples/superconscious/deterministic
```

The script is read-only and emits an AgentPlane-side import report. It does not seal evidence, mutate bundles, invoke agents, contact model providers, or write to external systems.

## Non-goals

- AgentPlane does not own recursive cognition planning.
- AgentPlane does not require raw private reasoning content.
- AgentPlane does not own SourceOS canonical schemas.
- AgentPlane does not replace Superconscious, SocioSphere, Model Router, Guardrail Fabric, Agent Registry, or Agent Machine.

## Next implementation step

Once this import report is stable, wire it into AgentPlane evidence sealing and replay lifecycle as a promoted `ReasoningReceipt` import path.
