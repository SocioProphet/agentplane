# Governed Runner Read-Only CI v0

## Purpose

This workflow validates the read-only governed-runner surface as a focused CI lane.

It exists so future changes to `sp-run`, the governed-runner smoke path, run-store inspection, receipt validation, or the local JSON tool adapter cannot silently regress the product-facing read-only loop.

## Workflow

```text
.github/workflows/governed-runner-readonly.yml
```

## Scope

The workflow runs on changes to:

- governed-runner CLI and helper tools
- governed-runner receipt validators
- governed-runner tests
- governed-runner schemas
- governed-runner fixtures
- runtime-governance docs
- the workflow itself

## Validation steps

The workflow validates generated and fixture-backed receipts:

```bash
python3 tools/sp_run.py preflight tests/fixtures/runs/governed-run-contract.valid.json \
  --generated-at 2026-05-22T12:20:00Z \
  --output /tmp/preflight-receipt.json
python3 tools/validate_preflight_receipt.py /tmp/preflight-receipt.json
python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.valid.json
python3 tools/validate_run_dossier.py tests/fixtures/runs/run-dossier/run-dossier.valid.json
! python3 tools/validate_run_dossier.py tests/fixtures/runs/run-dossier/run-dossier.ready-missing.invalid.json
```

It then exercises the read-only surface:

```bash
python3 -m pytest -q \
  tools/tests/test_sp_run_cli.py \
  tools/tests/test_sp_run_preflight_cli.py \
  tools/tests/test_sp_run_admit_cli.py \
  tools/tests/test_sp_run_delegate_surface.py \
  tools/tests/test_governed_runner_smoke.py \
  tools/tests/test_sp_run_run_store_inspection.py \
  tools/tests/test_governed_runner_tool_surface.py \
  tools/tests/test_sp_run_tool_adapter.py
```

## Boundary

This CI lane validates only the read-only governed-runner surface.

It does not add or validate:

- live agent execution
- verifier execution
- governed workspace mutation
- rollback restoration
- authority updates
- budget settlement

Those require separate policy-gated tranches.
