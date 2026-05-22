# sp-run admit v0

## Purpose

`sp-run admit` builds a read-only `AttemptAdmissionReceipt` from three governed inputs:

- `GovernedRunContract`
- `PreflightReceipt`
- Agent Registry `AgentAuthorityCurrentState`

It answers whether one attempt may run now, but it does not execute the attempt.

## Command

```bash
python3 tools/sp_run.py admit <governed-run-contract.json> \
  --preflight <preflight-receipt.json> \
  --authority-state <agent-authority-current-state.json> \
  --projected-cost-usd 0.25
```

Optional deterministic timestamp:

```bash
python3 tools/sp_run.py admit contract.json \
  --preflight preflight.json \
  --authority-state authority-state.json \
  --projected-cost-usd 0.25 \
  --generated-at 2026-05-22T12:30:00Z
```

Optional output file:

```bash
python3 tools/sp_run.py admit contract.json \
  --preflight preflight.json \
  --authority-state authority-state.json \
  --output attempt-admission-receipt.json
```

## Inputs

### GovernedRunContract

Provides:

- `run_id`
- budget limits
- policy bundle references
- authority grant reference
- TrustOps gate policy reference
- verification plan reference material

### PreflightReceipt

Provides:

- preflight outcome
- runtime action projection
- safety-preflight receipt reference

### AgentAuthorityCurrentState

Provides:

- current authority status
- authority effects
- authority state reference

## Admission behavior

The command emits `AttemptAdmissionReceipt v0.1`.

It admits only when:

- preflight outcome permits execution
- runtime action is `allow` or `warn`
- authority state maps to `unchanged` or `reduced`
- projected cost is within remaining budget
- remaining iterations and tokens are positive

It rejects when:

- projected cost exceeds remaining budget
- no iterations or tokens remain
- authority state is suspended or revoked
- preflight/runtime action is blocking

It emits `require-review` when:

- preflight or runtime action requires review

It emits `fail-closed` only for unmapped/unknown runtime action.

## Boundary

This command is read-only.

It does not:

- execute agents
- run verifier commands
- mutate files
- restore rollback state
- update authority
- settle actual budget/cost

Authority state remains owned by Agent Registry. Safety semantics remain owned by Guardrail Fabric. AgentPlane constructs the admission receipt from those inputs.

## Validation

```bash
python3 -m pytest -q tools/tests/test_sp_run_admit_cli.py
```

The tests cover:

- active authority + passing preflight admits
- suspended authority rejects
- review preflight emits `require-review`
- projected cost exceeding budget rejects

## Next step

After this command is stable, the governed-runner CLI surface is coherent enough for `prophet-cli` facade wiring:

```bash
prophet agentplane doctor
prophet agentplane preflight <contract.json>
prophet agentplane admit <contract.json> --preflight <preflight.json> --authority-state <authority.json>
prophet agentplane dossier <run_dir>
prophet agentplane validate-dossier <dossier.json>
```
