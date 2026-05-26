# RunDossier v0.1

## Purpose

`RunDossier` is the operator-facing summary artifact for a governed run.

It is derived from receipts only. It does not inspect raw logs, execute code, infer state from unstructured traces, or mutate the workspace.

The dossier gives operators one compact object that answers:

- what run was evaluated
- how many attempts exist
- whether the latest attempt was admitted
- what budget remains
- what runtime action and authority state applied
- what rollback evidence exists
- what restore-admission evidence exists, when present
- which receipts are missing
- what should happen next

## Boundary

AgentPlane owns this artifact because AgentPlane owns governed execution evidence, attempt admission, rollback evidence, restore-admission evidence, and run-level receipts.

Related planes:

- `guardrail-fabric` supplies TrustOps safety preflight and runtime action decisions.
- `agent-registry` supplies authority state and authority decisions.
- `SCOPE-D` and higher product surfaces consume dossiers as operator evidence.

## Evidence folder convention

The expected local run folder shape is:

```text
<run_dir>/
  governed-run-contract.json
  attempts/
    001/
      attempt-admission-receipt.json
      runtime-attempt-receipt.json
      verification-result.json
      rollback-boundary.json
      rollback-result.json
      restore-admission-receipt.json   # optional operator recovery panel source
```

The builder uses the latest attempt directory lexicographically.

## Builder

```bash
python3 tools/build_run_dossier.py <run_dir>
```

Optional output:

```bash
python3 tools/build_run_dossier.py <run_dir> --output run-dossier.json
```

Optional deterministic timestamp for tests:

```bash
python3 tools/build_run_dossier.py <run_dir> --generated-at 2026-05-22T12:10:00Z
```

## Dossier fields

Required fields include:

- `dossier_id`
- `run_id`
- `generated_at`
- `source_run_dir`
- `overall_status`
- `contract_ref`
- `attempt_count`
- `budget_summary`
- `latest_admission`
- `latest_rollback`
- `receipt_refs`
- `missing_receipts`
- `recommended_next_action`
- `dossier_hash`

Optional fields include:

- `latest_restore_admission`

## Restore-admission operator panel

When the latest attempt folder contains `restore-admission-receipt.json`, the dossier projects a `latest_restore_admission` panel. This panel is intentionally read-only. It does not perform restore, retry, rollback, resume, provider calls, workspace mutation, authority mutation, network access, or budget settlement.

The panel exposes the exact fields an operator needs before deciding whether recovery is safe:

```text
receipt_ref
admitted
admission_decision
requested_restore_action
halt_reason
verifier_state
side_effect_boundary
recovery_policy_posture
budget_remaining
admitted_actions
blocked_actions
operator_next_options
review_reason
fail_closed_reason
```

This implements the governed lifecycle rule established in #206: recovery state must be visible as typed evidence before any recovery implementation can mutate state.

## Status semantics

`overall_status` is one of:

- `ready`
- `blocked`
- `requires_review`
- `failed_closed`
- `incomplete`

A dossier cannot be `ready` if required receipts are missing.

## Validation

Validate the schema and a dossier fixture:

```bash
python3 tools/validate_run_dossier.py tests/fixtures/runs/run-dossier/run-dossier.valid.json
```

Validate that missing evidence cannot be hidden as ready:

```bash
! python3 tools/validate_run_dossier.py tests/fixtures/runs/run-dossier/run-dossier.ready-missing.invalid.json
```

Build from the synthetic run folder:

```bash
python3 tools/build_run_dossier.py tests/fixtures/runs/run-dossier/run --generated-at 2026-05-22T12:10:00Z
```

## Non-goals

This tranche does not define runtime execution.

It does not define an MCP surface.

It does not settle runtime costs.

It does not mutate authority state.

It does not perform rollback or restore.

It converts existing evidence into an operator-consumable summary.
