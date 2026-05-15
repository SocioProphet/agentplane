# Agentic Ops Runtime Budget Control v0.1

Status: proposed  
Owning repo: `SocioProphet/agentplane`  
Tracking issue: `SocioProphet/agentplane#161`

## Purpose

This contract adds runtime budget control to AgentPlane's agentic execution lane.

The existing Agentic PR Control Plane bounds issue-scoped implementation, review, merge gates, and ledger evidence. Runtime budget control adds the missing accounting layer for stochastic agent trajectories: persona policy, workload signature, UCO caps, degradation thresholds, per-step cost attribution, and trajectory event linkage.

This is not a scheduler, dashboard, model gateway, or policy engine. It is the AgentPlane contract layer that lets those systems interoperate without inventing incompatible budget records.

## Core position

Agentic ops is a workload class with a stochastic UCO vector. A governed agentic run must declare the persona policy, workload signature, budget ledger, and trajectory event stream before downstream telemetry can be trusted.

The control goal is not merely to minimize cost. The control goal is to bound cost variance under policy, evidence, and service-level constraints.

## Contract objects

### `AgenticOpsPersonaPolicy`

Defines objective weights, default caps, agentic axes, data-class allowlist, model/cache policy, policy references, and telemetry refs. Objective weights must sum to `1.0`; the validator enforces this invariant.

### `AgenticOpsWorkloadSignature`

Describes scenario, data class, sensitivity, expected trajectory length, expected tool calls, read/write ratio, hotness skew, reversibility requirement, human-checkpoint posture, and validation expectations.

### `AgenticOpsBudgetLedger`

Records admitted caps, observed spend, remaining budget, degradation posture, and policy references across prompt tokens, completion tokens, cached tokens, verification tokens, tool calls, wall-clock seconds, and dollars.

### `AgenticOpsTrajectoryEvent`

Records one step in the agentic run with UCO attribution, cache attribution, decision references, previous event hash, and current event hash.

## Ownership boundaries

| Surface | Owner | Boundary |
|---|---|---|
| Work-order lifecycle and run evidence | `SocioProphet/agentplane` | Owns these contracts and the execution/evidence lane. |
| Diff hygiene, merge policy, and budget-policy verdicts | `SocioProphet/policy-fabric` | AgentPlane references verdicts; it does not redefine policy authority. |
| Allow/deny/redact/escalate runtime decisions | `SocioProphet/guardrail-fabric` | AgentPlane records decision refs; Guardrail Fabric owns the decision ABI. |
| Aggregated operational intelligence | `SocioProphet/global-devsecops-intelligence` | Consumes trajectory and ledger records for service metrics and drift detection. |
| Operator dashboard and workroom steering | `SocioProphet/sociosphere` | Consumes summarized state; does not become the source of truth. |
| Mesh skills, coordinates, cairns, and TriTRPC validation lanes | `SourceOS-Linux/sourceos-spec` | Provides OS/mesh validation semantics; AgentPlane preserves compatible refs. |

## Admission and degradation model

Minimal admission outcomes are `admit`, `admit_with_degradation`, and `reject`.

Minimal degradation actions are `switch_to_cheaper_model`, `disable_model_cascade`, `reduce_verification_sampling`, `force_plan_then_execute`, `cap_remaining_replans`, `terminate_with_partial_result`, and `require_human_checkpoint`.

## Prefix-cache accounting

Prompt caching is represented explicitly because agentic trajectories repeat stable context. The contracts distinguish prompt tokens, cached prefix tokens, cache-hit tokens, and completion tokens.

## v0.1 non-goals

No production scheduler, provider SDK integration, live model router, dashboard, autonomous merge authority, Policy Fabric replacement, Guardrail Fabric replacement, or SourceOS cairn implementation in this repo.

## Definition of done for this tranche

This tranche is complete when schema-backed examples and a stdlib validator prove the contract shape and critical invariants.
