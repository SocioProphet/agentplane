# RestoreAdmissionReceipt v0.1

## Purpose

`RestoreAdmissionReceipt v0.1` is AgentPlane's pre-execution admission result for one governed restore, recovery, resume, or retry attempt.

It exists for the rollback-restore seam tracked in `SocioProphet/agentplane#206`: a recovery attempt must not be admitted from raw logs alone. The operator needs an explicit receipt that exposes the original-attempt context, halt reason, verifier state, budget posture, admissible next actions, blocked actions, and the final admission decision.

The receipt answers one question before any restore action executes:

> Given the prior attempt and current recovery posture, is this restore action allowed to run now?

## Boundary

AgentPlane owns this receipt because AgentPlane owns governed runtime admission and evidence-bearing execution boundaries.

Related surfaces:

- `OriginalAttemptContext v0.1` records the previous attempt phase and side-effect boundary.
- `AttemptAdmissionReceipt v0.1` admits the ordinary governed runtime attempt.
- `VerificationExecutionReceipt v0.1` and runtime receipts describe what execution evidence exists.
- `BudgetSettlementReceipt v0.1` and budget estimates describe whether a next attempt remains inside budget.
- rollback boundary/result receipts describe rollback scope and rollback outcome.

This receipt composes those surfaces into an operator-facing recovery admission decision. It does not replace them.

## Required fields

The contract requires:

```text
receipt_id
restore_attempt_id
run_id
governed_run_contract_ref
original_attempt_context_ref
requested_restore_action
halt_reason
verifier_state
budget_remaining
budget_required
side_effect_boundary
recovery_policy_posture
admitted
admission_decision
admitted_actions
blocked_actions
operator_next_options
evidence_refs
issued_at
receipt_hash
```

## Recovery actions

`requested_restore_action` is one of:

```text
retry_same_payload
retry_replanned_payload
resume_from_checkpoint
rollback_only
rollback_then_retry
operator_review_only
```

`operator_review_only` is intentionally non-executable. It may appear as the requested posture when the system can only surface a review state to the operator.

## Admission decisions

`admission_decision` is one of:

```text
admit
require-review
deny
fail-closed
```

`admitted=true` is valid only with `admission_decision=admit`.

`require-review`, `deny`, and `fail-closed` are not autonomous admissions.

`fail-closed` requires `fail_closed_reason`.

## Operator-facing state

The receipt makes four recovery facts explicit:

```text
halt_reason
verifier_state
budget_remaining
operator_next_options
```

This is the operator seam: a governed runner should not ask an operator to decide from raw logs when the recovery controller can emit a typed admission receipt.

## Policy interpretation

| Condition | Admission result |
|---|---|
| `side_effect_boundary = none`, `recovery_policy_posture = eligible_for_retry`, verifier passed, and budget sufficient | `admit` |
| `side_effect_boundary = possible` | `require-review` |
| `side_effect_boundary = unknown` | `require-review` |
| `side_effect_boundary = confirmed` | `deny` or `fail-closed` |
| `recovery_policy_posture = requires_review` | `require-review` |
| `recovery_policy_posture = blocked` | `deny` or `fail-closed` |
| `verifier_state = stale/missing/inconclusive` | no autonomous admission |
| `verifier_state = failed` | no autonomous admission |
| required budget exceeds remaining budget | no autonomous admission |
| `halt_reason = unknown` | no autonomous admission and review reason required |

## Validator invariants

The validator enforces:

- schema is strict JSON Schema draft 2020-12;
- restore receipts must reference an `OriginalAttemptContext`;
- `evidence_refs.original_attempt_context_ref` must match the top-level `original_attempt_context_ref`;
- `admitted=true` requires `admission_decision=admit`;
- non-admitted receipts cannot expose `admitted_actions`;
- admitted receipts must include the requested executable action in `admitted_actions`;
- an action cannot appear in both `admitted_actions` and `blocked_actions`;
- restore execution cannot be admitted when required budget exceeds remaining budget;
- restore execution cannot be admitted when verifier state is not `passed`;
- possible or unknown side-effect boundary requires review;
- confirmed side-effect boundary must deny or fail closed;
- blocked recovery posture must deny or fail closed;
- unknown halt reason requires review reason;
- fail-closed requires a fail-closed reason.

## Fixtures

Valid fixtures:

```text
tests/fixtures/receipts/restore-admission-receipt.queued-none-admitted.valid.json
tests/fixtures/receipts/restore-admission-receipt.started-possible-review.valid.json
tests/fixtures/receipts/restore-admission-receipt.completed-confirmed-denied.valid.json
```

Invalid fixtures:

```text
tests/fixtures/receipts/restore-admission-receipt.missing-original-context.invalid.json
tests/fixtures/receipts/restore-admission-receipt.stale-verifier-admitted.invalid.json
tests/fixtures/receipts/restore-admission-receipt.insufficient-budget-admitted.invalid.json
tests/fixtures/receipts/restore-admission-receipt.unknown-halt-no-review.invalid.json
tests/fixtures/receipts/restore-admission-receipt.possible-side-effect-admitted.invalid.json
```

## Validation

```bash
python3 tools/validate_restore_admission_receipt.py tests/fixtures/receipts/restore-admission-receipt.queued-none-admitted.valid.json
```

## Non-goals

This receipt does not execute a restore, retry, rollback, or resume action.

It does not mutate workspace state, provider state, authority state, budget ledgers, or external systems.

It does not settle budget. Budget settlement remains a downstream receipt surface.

It does not infer safety from logs alone. Recovery admission must be receipt-bound.
