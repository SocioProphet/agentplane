# BudgetSettlementReceipt v0.1

## Purpose

`BudgetSettlementReceipt v0.1` separates budget estimate, budget admission, and budget settlement.

Governed-runner v0.1 already records budget estimates inside `GovernedRunContract` and `AttemptAdmissionReceipt`. That is not the same as settlement. A future runtime attempt needs a distinct receipt for actual measured resource use so operators can audit whether an admitted attempt stayed within the budget it was admitted under.

This tranche defines the receipt, fixtures, validator, tests, and Makefile target only. It does not add runtime execution, live billing integration, provider API calls, token metering, authority updates, or rollback restore.

## Boundary model

| Layer | Artifact | Meaning |
|---|---|---|
| Estimate | `GovernedRunContract` / `AttemptAdmissionReceipt.budget_estimate` | Projected cost and remaining budget used for admission |
| Admission | `AttemptAdmissionReceipt` | Decision that an attempt may proceed under pre-execution gates |
| Settlement | `BudgetSettlementReceipt` | Post-attempt record of actual measured resource use and overrun status |

A settlement receipt must not be used as admission authority.

An admission receipt must not be treated as actual cost settlement.

## Receipt fields

Required fields:

- `settlement_id`
- `run_id`
- `attempt_id`
- `admission_receipt_ref`
- `settled_at`
- `estimate`
- `actuals`
- `settlement_status`
- `overrun`
- `settlement_provenance`
- `receipt_hash`

## Estimate block

The `estimate` block records the budget basis used before execution:

- `projected_cost_usd`
- `remaining_budget_usd`
- optional `remaining_iterations`
- optional `remaining_tokens`
- `estimate_provenance`

The expected provenance is normally the corresponding `AttemptAdmissionReceipt`.

## Actuals block

The `actuals` block records measured or synthetic actual use:

- `tokens_in`
- `tokens_out`
- `tool_calls`
- `wall_clock_ms`
- `cost_usd`

All actual counters must be non-negative.

## Settlement status

Allowed values:

- `settled`
- `overrun`
- `missing_actuals`
- `invalid_actuals`
- `fail-closed`

`settled` means actual cost is within the projected cost.

`overrun` means actual cost exceeded the projected cost and is explicitly reported as such.

`missing_actuals`, `invalid_actuals`, and `fail-closed` require `fail_closed_reason`.

## Overrun consistency

The validator enforces:

```text
overrun.estimated_cost_usd == estimate.projected_cost_usd
overrun.actual_cost_usd == actuals.cost_usd
overrun.over_budget == actuals.cost_usd > estimate.projected_cost_usd
```

A hidden overrun is invalid. A receipt cannot claim `settled` if actual cost exceeds projected cost.

## Fixtures

Valid fixtures:

```text
tests/fixtures/receipts/budget-settlement-receipt.settled.valid.json
tests/fixtures/receipts/budget-settlement-receipt.overrun.valid.json
```

Invalid fixtures:

```text
tests/fixtures/receipts/budget-settlement-receipt.missing-admission-ref.invalid.json
tests/fixtures/receipts/budget-settlement-receipt.missing-actuals.invalid.json
tests/fixtures/receipts/budget-settlement-receipt.negative-actual.invalid.json
tests/fixtures/receipts/budget-settlement-receipt.hidden-overrun.invalid.json
```

## Validation

```bash
make validate-budget-settlement-receipt
python3 -m pytest -q tools/tests/test_budget_settlement_receipt.py
```

Direct validation:

```bash
python3 tools/validate_budget_settlement_receipt.py \
  tests/fixtures/receipts/budget-settlement-receipt.settled.valid.json
```

## Non-goals

This contract does not add:

- live billing integration;
- provider API calls;
- actual token metering implementation;
- runtime execution;
- verifier execution;
- authority update;
- rollback restore;
- workspace mutation;
- admission authority.

Runtime settlement integration must be a separate implementation tranche after this receipt boundary is accepted.
