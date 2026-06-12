# Agentic Runtime Semantics — Design Contract v0

## Overview

Every state transition in a durable agentic execution produces an `AgenticRuntimeState` evidence artifact. The schema is the single source of truth for what transitions are valid, what sub-artifacts they require, and what metadata is preserved.

## 14-State Node Lifecycle

```
created → queued → leased → running
                                 ├── succeeded
                                 ├── failed → retry_scheduled → requeued → (leased again)
                                 ├── quarantined  (control signal required)
                                 ├── waiting_for_human  (control signal required)
                                 ├── waiting_for_resource
                                 ├── pruned
                                 └── superseded
reconciled  (terminal — missing/failed signal delivery resolved)
```

| State | Meaning |
|---|---|
| `created` | Node instantiated; not yet placed in queue |
| `queued` | Admitted to execution queue |
| `leased` | A worker has taken the lease |
| `running` | Actively executing |
| `succeeded` | Execution completed with evidence |
| `failed` | Execution error; may trigger retry |
| `retry_scheduled` | Retry policy applied; delay before requeue (**requires `retry_policy`**) |
| `requeued` | Back in queue after retry delay |
| `pruned` | Branch abandoned by `prune_branch` control signal |
| `quarantined` | Anomaly detected; execution suspended (**requires `control_signal`**) |
| `waiting_for_human` | Human approval gate (**requires `control_signal`**) |
| `waiting_for_resource` | Blocked on external dependency |
| `superseded` | A newer run has taken authority |
| `reconciled` | Missing/failed signal delivery resolved via reconcile signal |

## Control Signals

Control signals are **durable and idempotent** — each carries an `idempotency_key`. Duplicate delivery is safe. Undelivered signals must be reconciled via `reconcile_missing_delivery` or `reconcile_failed_delivery` signals.

| Signal | Effect |
|---|---|
| `prune_branch` | Terminate branch; transition to `pruned` |
| `requeue_after_delay` | Delay then requeue; requires `requeue_delay_seconds` |
| `quarantine` | Suspend to `quarantined`; human review required before release |
| `wait_for_human_approval` | Pause to `waiting_for_human`; resume on approval receipt |
| `cancel_supersede` | Transition to `superseded` |
| `retry_with_policy` | Apply retry policy; transition to `retry_scheduled` |
| `reconcile_missing_delivery` | Recover from undelivered signal |
| `reconcile_failed_delivery` | Recover from failed signal delivery |

## Join / Fanout Strategies

### Fanout strategies

| Strategy | Description |
|---|---|
| `parallel_all` | All branches launch simultaneously |
| `parallel_bounded` | Max `concurrency_limit` branches active at a time |
| `sequential` | Branches execute one at a time |
| `priority_ordered` | Branches ordered by priority; higher-priority first |

Every fanout record names its `join_point_ref` — the JoinRecord artifact that will collect results.

### Join strategies

| Strategy | Resolution condition |
|---|---|
| `all_success` | All participating nodes must succeed |
| `all_terminal` | All participating nodes must reach a terminal state (any) |
| `quorum` | `quorum_threshold` fraction must succeed |
| `first_success` | First node to succeed wins; others pruned |
| `best_of_n` | Wait for `best_of_n` nodes, pick highest score |
| `deadline_reached` | Accept whatever is done at the deadline |
| `budget_exhausted` | Accept whatever is done when budget runs out |
| `human_selected_subset` | Human picks which nodes proceed; requires `human_selection_ref` |
| `risk_approved_subset` | Risk authority approves subset; requires `risk_approval_ref` |

## Retry Policy

Retry scope is **per-node, per-tool, per-provider, per-risk-class, or per-graph** — not graph-only. This allows fine-grained retry bounds: a high-risk tool can have `max_attempts: 1` while the surrounding graph allows 3.

Backoff strategies: `immediate`, `fixed_delay`, `exponential_backoff`, `policy_gated`.

## Scheduling Triggers

All triggers are cancellable by default. Pause/resume is opt-in per trigger.

| Trigger | Source |
|---|---|
| `cron` | Time schedule (requires `cron_expression`) |
| `github_event` | GitHub webhook event |
| `filesystem_event` | File/directory change |
| `webhook` | Arbitrary HTTP push |
| `ci_status` | CI pipeline state change |
| `policy_event` | Policy fabric decision event |
| `budget_event` | Budget threshold reached |
| `memory_drift_event` | Agent memory drift detected |
| `sync_conflict_event` | State sync conflict detected |
| `human_approval_event` | Human approval artifact received |

## Evidence guarantees

Every `AgenticRuntimeState` artifact:

- Is produced per-transition (not batched)
- Carries `policy_decision_ref` scoping the transition authority
- Carries `non_claims` scoping what the artifact does not assert
- References `evidence_refs` linking to HellGraph evidence nodes produced by the transition

No existing AgentPlane artifact/replay guarantees are reduced by this extension.
