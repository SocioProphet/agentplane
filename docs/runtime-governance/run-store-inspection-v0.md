# Governed Runner Run-Store Inspection v0

## Purpose

This tranche adds read-only inspection commands for governed-run evidence folders.

It lets operators enumerate and inspect generated evidence without executing agents, running verifiers, mutating files, restoring rollback state, updating authority, or settling budget.

## Commands

List run folders under a run-store root:

```bash
sp-run list --runs-root .socioprophet/runs
```

Summarize one run folder:

```bash
sp-run status .socioprophet/runs/governed-run-alpha-001
```

Inspect one run folder and enumerate receipt files:

```bash
sp-run inspect .socioprophet/runs/governed-run-alpha-001
```

Through the Prophet facade:

```bash
prophet governed-runner list --runs-root .socioprophet/runs
prophet governed-runner status .socioprophet/runs/governed-run-alpha-001
prophet governed-runner inspect .socioprophet/runs/governed-run-alpha-001
```

## Output records

### RunList

`sp-run list` emits:

- `recordType = RunList`
- `runs_root`
- `count`
- `runs[]`

Each run summary includes:

- `run_id`
- `run_dir`
- `overall_status`
- `attempt_count`
- `missing_receipts`

### RunStatus

`sp-run status` emits:

- `recordType = RunStatus`
- `run_id`
- `run_dir`
- `overall_status`
- `attempt_count`
- `latest_admission`
- `latest_rollback`
- `budget_summary`
- `missing_receipts`
- `recommended_next_action`

### RunInspection

`sp-run inspect` emits:

- `recordType = RunInspection`
- `run_id`
- `run_dir`
- embedded `RunDossier`
- `receipt_files[]`
- `non_goals[]`

## Evidence source

Inspection derives state from the same receipt-derived dossier builder used by `sp-run dossier`.

No raw logs are interpreted.

No commands are executed.

## Boundary

These commands are read-only.

They do not:

- execute agents
- run verifier commands
- mutate governed workspace files
- restore rollback state
- update authority
- settle budget

## Validation

```bash
python3 -m pytest -q tools/tests/test_sp_run_run_store_inspection.py
```

The tests build a smoke evidence folder and then exercise:

- `sp-run list`
- `sp-run status`
- `sp-run inspect`
