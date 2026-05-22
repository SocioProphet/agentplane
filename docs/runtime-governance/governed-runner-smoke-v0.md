# Governed Runner Smoke v0

## Purpose

`tools/run_governed_runner_smoke.py` provides a deterministic, non-mutating smoke path for the governed-runner control spine.

It proves that the read-only operator loop composes:

```text
GovernedRunContract
  -> PreflightReceipt
  -> AttemptAdmissionReceipt
  -> evidence folder
  -> RunDossier
  -> smoke summary
```

## Command

```bash
python3 tools/run_governed_runner_smoke.py \
  --output-dir .socioprophet/smoke/governed-runner \
  --generated-at 2026-05-22T12:45:00Z
```

The command writes:

```text
<output-dir>/
  run/
    governed-run-contract.json
    attempts/
      001/
        preflight-receipt.json
        attempt-admission-receipt.json
        runtime-attempt-receipt.json
        verification-result.json
        rollback-boundary.json
        rollback-result.json
  run-dossier.json
  smoke-result.json
```

## Source fixtures

The smoke path uses existing checked-in fixtures and builders:

- `tests/fixtures/runs/governed-run-contract.valid.json`
- `tests/fixtures/authority/agent-authority-current-state.active.json`
- `tests/fixtures/receipts/rollback-boundary.valid.json`
- `tests/fixtures/receipts/rollback-result.valid.json`
- synthetic runtime and verification fixtures from the run-dossier fixture set
- `tools/sp_run.py` preflight and admission builders
- `tools/build_run_dossier.py`

## Output semantics

The smoke result reports:

- `ok`
- `run_id`
- `preflight_outcome`
- `admission_decision`
- `admitted`
- `dossier_status`
- `missing_receipts`
- generated artifact paths
- non-goals

A passing smoke result requires:

- preflight outcome is `pass`
- admission decision is `admit`
- attempt is admitted
- dossier status is `ready`
- no missing receipts

## Boundary

This smoke path is read-only with respect to governed execution.

It does not:

- execute agents
- run verifier commands
- mutate project files beyond writing smoke artifacts to the requested output directory
- restore rollback state
- update authority state
- settle budget

## Validation

```bash
python3 -m pytest -q tools/tests/test_governed_runner_smoke.py
```

## Relationship to prophet-cli

The smoke path gives the `prophet governed-runner ...` facade a deterministic local evidence target once `sp-run` is installed and delegated.

The facade remains in `prophet-cli`; the governed-runner implementation and smoke evidence path remain in AgentPlane.
