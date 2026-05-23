# VerificationExecutionReceipt v0.1

## Purpose

`VerificationExecutionReceipt v0.1` defines a receipt boundary for future verifier-result evidence.

This tranche is schema, fixture, validator, test, and documentation work only. It does not add a runner or any runtime path.

## Boundary model

The receipt records one synthetic verifier result after all preconditions are already satisfied.

Required referenced inputs:

- `GovernedRunContract`
- `PreflightReceipt`
- Agent Registry authority state
- `AttemptAdmissionReceipt`
- allowlisted verifier command reference

A valid v0.1 receipt requires:

```text
admission_decision = admit
preflight_outcome = pass
runtime_action = allow
authority_decision is not suspended or revoked
verifier_command.allowlisted = true
verifier_command.network_mode = off
verifier_command.mutation_mode = none
```

## Receipt fields

Required fields:

- `execution_id`
- `run_id`
- `attempt_id`
- `governed_run_contract_ref`
- `admission_receipt_ref`
- `preflight_receipt_ref`
- `authority_state_ref`
- `verifier_command_ref`
- `verifier_command`
- `safety_context`
- `execution_status`
- `started_at`
- `ended_at`
- `exit_code`
- `stdout_ref`
- `stderr_ref`
- `artifact_refs`
- `receipt_hash`

## Verifier command block

The command block records metadata for the admitted verifier command.

For v0.1, only these modes are valid:

```text
network_mode = off
mutation_mode = none
allowlisted = true
```

## Safety context block

The safety context records the already-computed admission boundary.

Rejected, require-review, suspended, or revoked contexts are invalid for a completed verifier-result receipt.

## Fixtures

Valid fixture:

```text
tests/fixtures/receipts/verification-execution-receipt.completed.valid.json
```

Invalid fixtures:

```text
tests/fixtures/receipts/verification-execution-receipt.missing-admission-ref.invalid.json
tests/fixtures/receipts/verification-execution-receipt.rejected-admission.invalid.json
tests/fixtures/receipts/verification-execution-receipt.require-review-admission.invalid.json
tests/fixtures/receipts/verification-execution-receipt.non-allowlisted-command.invalid.json
tests/fixtures/receipts/verification-execution-receipt.open-mode.invalid.json
tests/fixtures/receipts/verification-execution-receipt.write-mode.invalid.json
```

## Validation

```bash
make validate-verification-execution-receipt
python3 -m pytest -q tools/tests/test_verification_execution_receipt.py
```

Direct validation:

```bash
python3 tools/validate_verification_execution_receipt.py \
  tests/fixtures/receipts/verification-execution-receipt.completed.valid.json
```

## Non-goals

This contract does not add:

- verifier-result production;
- provider calls;
- network access;
- workspace changes;
- rollback restore;
- authority update;
- budget settlement integration.

Any future runtime implementation must be a separate policy-gated tranche built on this receipt boundary.
