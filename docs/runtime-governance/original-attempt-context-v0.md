# OriginalAttemptContext v0.1

## Purpose

`OriginalAttemptContext v0.1` records the lifecycle posture of the original governed-runner attempt before any future restore, recovery, or retry policy is evaluated.

It exists because recovery semantics depend on what happened before recovery was requested. A queued attempt, an admitted-but-not-started attempt, and a started attempt with possible side effects are not equivalent.

## Core rule

Restore and retry policy must key off the pair:

```text
original_attempt_phase + side_effect_boundary
```

`original_attempt_phase` alone is insufficient because `started` is ambiguous. A started attempt might fail before any side effect, or it might fail after partial external effects.

## Required fields

The contract requires:

```text
original_attempt_ref
original_attempt_phase
side_effect_boundary
retry_posture
original_attempt_status_source
recovery_policy_posture
```

Optional refs preserve evidence provenance:

```text
original_admission_ref
original_preflight_ref
original_execution_ref
original_runtime_receipt_ref
original_verification_receipt_ref
```

## Enumerations

Attempt phase:

```text
queued | admitted | started | completed | failed | skipped | unknown
```

Side-effect boundary:

```text
none | possible | confirmed | unknown
```

Retry posture:

```text
safe_retry | review_required | do_not_retry
```

Status source:

```text
queue_state
attempt_admission_receipt
verification_execution_receipt
runtime_receipt
run_dossier
operator_asserted
inferred_fallback
unknown
```

Recovery policy posture:

```text
eligible_for_retry | requires_review | blocked
```

## Policy interpretation

| Phase | Side-effect boundary | Retry posture | Policy posture |
|---|---|---|---|
| `queued` | `none` | `safe_retry` | `eligible_for_retry` |
| `admitted` | `none` | `review_required` | `requires_review` |
| `started` | `none` | `review_required` | `requires_review` |
| `started` / `failed` | `possible` | `review_required` | `requires_review` |
| `started` / `failed` | `confirmed` | `do_not_retry` | `blocked` |
| `completed` | `confirmed` | `do_not_retry` | `blocked` |
| `unknown` | any | `review_required` | `requires_review` |
| any | `unknown` | `review_required` | `requires_review` |

## Validator invariants

The validator enforces:

- queued attempts cannot carry admission or execution refs;
- queued attempts must use `side_effect_boundary = none`;
- queued + none maps to `safe_retry` and `eligible_for_retry`;
- admitted attempts require `original_admission_ref`;
- admitted attempts cannot claim execution receipts;
- started/completed/failed attempts require execution or runtime evidence refs;
- completed attempts require `side_effect_boundary = confirmed`;
- completed + confirmed maps to `do_not_retry` and `blocked`;
- possible/confirmed side effects cannot map to `safe_retry`;
- unknown phase or unknown boundary requires review;
- review-required and do-not-retry postures require a review reason.

## Fixtures

Valid fixtures:

```text
tests/fixtures/receipts/original-attempt-context.queued-safe.valid.json
tests/fixtures/receipts/original-attempt-context.started-possible.valid.json
tests/fixtures/receipts/original-attempt-context.completed-confirmed.valid.json
tests/fixtures/receipts/original-attempt-context.unknown-review.valid.json
```

Invalid fixtures:

```text
tests/fixtures/receipts/original-attempt-context.completed-missing-execution.invalid.json
tests/fixtures/receipts/original-attempt-context.queued-with-execution.invalid.json
tests/fixtures/receipts/original-attempt-context.confirmed-safe-retry.invalid.json
```

## Validation

```bash
python3 tools/validate_original_attempt_context.py tests/fixtures/receipts/original-attempt-context.queued-safe.valid.json
python3 -m pytest -q tools/tests/test_original_attempt_context.py
```

## Boundary

This contract does not add:

- restore implementation;
- recovery action execution;
- workspace mutation;
- provider calls;
- network access;
- authority mutation;
- budget settlement integration.

Any future restore or recovery implementation must consume this context and must not infer retry posture from phase alone.
