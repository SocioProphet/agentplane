# sp-run preflight v0

## Purpose

`sp-run preflight` is the first read-only command that projects a `GovernedRunContract` into a pre-execution safety posture.

It validates the contract, derives the inputs that belong to Guardrail Fabric safety preflight, and emits a `PreflightReceipt`.

This command does not execute agents, run verifier commands, mutate files, restore rollback state, update authority, or settle budget.

## Command

```bash
python3 tools/sp_run.py preflight <governed-run-contract.json>
```

With deterministic timestamp:

```bash
python3 tools/sp_run.py preflight tests/fixtures/runs/governed-run-contract.valid.json \
  --generated-at 2026-05-22T12:20:00Z
```

With output file:

```bash
python3 tools/sp_run.py preflight contract.json --output preflight-receipt.json
```

## Receipt

The command emits `PreflightReceipt v0.1`:

- `receipt_id`
- `run_id`
- `governed_run_contract_ref`
- `mode = readonly_projection`
- `authoritative_safety_owner = SocioProphet/guardrail-fabric`
- `outcome = pass | require-review | block`
- `runtime_action = allow | require-review | block`
- `safety_preflight_input`
- `findings`
- `generated_at`
- `receipt_hash`

## Boundary

This command is an AgentPlane projection, not a replacement for Guardrail Fabric.

Guardrail Fabric remains the authoritative owner of safety preflight semantics. The receipt explicitly records:

```json
"authoritative_safety_owner": "SocioProphet/guardrail-fabric"
```

## Projection behavior

The command currently detects:

- invalid governed-run contract shape: `block`
- blocked verifier command patterns: `block`
- network target while `network_mode=off`: `block`
- non-allowlisted network target while `network_mode=allowlisted`: `block`
- `network_mode=open`: `require-review`
- unsafe path patterns: `block`
- `approval_policy.external_writes=true`: `require-review`

## Validation

CLI tests:

```bash
python3 -m pytest -q tools/tests/test_sp_run_preflight_cli.py
```

Validate a generated receipt:

```bash
python3 tools/sp_run.py preflight tests/fixtures/runs/governed-run-contract.valid.json \
  --generated-at 2026-05-22T12:20:00Z \
  --output /tmp/preflight-receipt.json
python3 tools/validate_preflight_receipt.py /tmp/preflight-receipt.json
```

## Non-goals

This command does not perform attempt admission.

It does not issue `AttemptAdmissionReceipt`.

It does not execute a run.

It does not mutate authority state.

It does not replace Guardrail Fabric safety preflight.

It provides a read-only bridge from `GovernedRunContract` to the safety-preflight inputs and projected action needed by the next admission layer.
