# Synthetic Verification Receipt Producer v0

## Purpose

`tools/build_synthetic_verification_receipt.py` builds a synthetic `VerificationExecutionReceipt v0.1` from explicit fixture/reference inputs.

It exists as the first safe producer for the verifier-result receipt boundary.

## Boundary

This tool only writes a JSON receipt and validates it with `tools/validate_verification_execution_receipt.py`.

It does not:

- execute verifier commands;
- invoke a shell;
- accept arbitrary command input;
- contact providers;
- use network access;
- mutate workspace files;
- update authority;
- perform recovery actions;
- settle budget.

## Inputs

Required references:

```text
--execution-id
--run-id
--attempt-id
--governed-run-contract-ref
--admission-receipt-ref
--preflight-receipt-ref
--authority-state-ref
```

The verifier plan is fixed to an allowlisted synthetic plan:

```text
pytest-sp-run-cli
```

The plan records:

```text
network_mode = off
mutation_mode = none
allowlisted = true
```

## Required safety context

The builder requires:

```text
admission_decision = admit
preflight_outcome = pass
runtime_action = allow
authority_decision != suspended/revoked
```

Rejected, review-required, blocked, or suspended contexts fail before a receipt is written.

## Validation

```bash
python3 tools/build_synthetic_verification_receipt.py \
  --output /tmp/synthetic-verification-receipt.json \
  --execution-id verification-execution-receipt:synthetic-alpha-001 \
  --run-id governed-run-alpha-001 \
  --attempt-id attempt:governed-run-alpha-001:001 \
  --governed-run-contract-ref governed-run-contract:governed-run-alpha-001 \
  --admission-receipt-ref attempt-admission-receipt:governed-run-alpha-001:001 \
  --preflight-receipt-ref preflight-receipt:governed-run-alpha-001 \
  --authority-state-ref agent-authority-current-state:agent-alpha:active

python3 tools/validate_verification_execution_receipt.py /tmp/synthetic-verification-receipt.json
python3 -m pytest -q tools/tests/test_synthetic_verification_receipt.py
```

## Next boundary

Any real verifier runner must be a separate policy-gated issue and PR.
