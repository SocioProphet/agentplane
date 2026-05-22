# AttemptAdmissionReceipt v0.1

## Purpose

`AttemptAdmissionReceipt` is AgentPlane's pre-execution admission result for one governed runtime attempt.

It consumes the `GovernedRunContract` together with safety preflight, authority state, TrustOps runtime action mapping, and budget estimate. The receipt answers one question before execution:

> Is this attempt allowed to run now?

The answer must be evidence-bearing. Rejections and fail-closed outcomes are receipts, not silent exits.

## Boundary

AgentPlane owns this receipt because AgentPlane owns governed execution and attempt admission.

Related planes:

- `guardrail-fabric` produces safety preflight decisions and TrustOps runtime action mappings.
- `agent-registry` owns authority grants, authority decisions, and current authority state.
- `sociosphere` coordinates workflow admission state.
- `SCOPE-D` consumes attempt evidence and run dossiers.

## Required fields

- `receipt_id`
- `attempt_id`
- `run_id`
- `governed_run_contract_ref`
- `admitted`
- `admission_decision`
- `reason_code`
- `safety_preflight_ref`
- `safety_preflight_outcome`
- `authority_state_ref`
- `authority_decision`
- `trustops_runtime_action_ref`
- `runtime_action`
- `budget_estimate`
- `issued_at`
- `receipt_hash`

## Admission decisions

`admission_decision` is one of:

- `admit`
- `reject`
- `require-review`
- `fail-closed`

`admitted=true` is valid only with `admission_decision=admit`.

`require-review` is not an autonomous admission.

`reject` and `fail-closed` cannot admit an attempt.

## Blocking inputs

An attempt must not be admitted when any of the following are true:

- projected cost exceeds remaining budget
- no remaining iterations
- no remaining tokens
- safety preflight outcome is `quarantine`, `block`, `rollback`, or `revoke`
- authority decision is `suspended` or `revoked`
- runtime action is `quarantine`, `block`, `rollback`, or `revoke`

When safety or runtime action is `require-review`, the admission decision must be `require-review`.

When admission is `fail-closed`, `fail_closed_reason` is required.

## Budget estimate

`budget_estimate` includes:

- `projected_cost_usd`
- `remaining_budget_usd`
- `remaining_iterations`
- `remaining_tokens`
- `estimate_provenance = actual | estimated | unavailable`

Budget estimates are pre-execution admission evidence, not settlement evidence. Runtime settlement belongs to a later runtime attempt receipt.

## Input references

`input_refs` can bind the admission decision back to:

- `policy_bundle_ref`
- `authority_grant_ref`
- `trustops_gate_policy_ref`
- `verification_plan_ref`

These are optional at schema level because some callers may bind them via the `GovernedRunContract`, but preferred for operator dossiers.

## Validation

```bash
make validate-attempt-admission-receipt
```

The validation target checks:

- schema JSON parses
- valid admission passes
- budget exceeded cannot admit
- safety block cannot admit
- suspended authority cannot admit
- require-review cannot be admitted autonomously
- fail-closed requires `fail_closed_reason`

## Non-goals

This receipt does not execute the attempt.

It does not settle runtime cost.

It does not mutate agent authority.

It does not perform rollback. Rollback boundary and rollback outcome receipts are a later tranche.
