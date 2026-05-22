# RollbackBoundary and RollbackResult v0.1

## Purpose

Rollback receipts make repo-state recovery evidence-bearing.

This tranche defines two AgentPlane receipt classes:

- `RollbackBoundary`: records the repo state before an effectful attempt.
- `RollbackResult`: records whether the current repo state matches the recorded boundary after recovery handling.

Together they make rollback auditable without relying on prose logs.

## Boundary

AgentPlane owns these receipts because AgentPlane owns governed execution, attempt evidence, replay material, and run receipts.

This tranche is intentionally conservative:

- `capture_rollback_boundary.py` is read-only.
- `record_rollback_result.py` is read-only.
- No workspace mutation is performed by this tranche.
- Future restore execution must be explicitly policy-gated by AttemptAdmissionReceipt and Agent Registry authority state.

## RollbackBoundary

Required fields:

- `boundary_id`
- `run_id`
- `attempt_id`
- `repo_root`
- `captured_at`
- `strategy`
- `head_ref`
- `tracked_dirty_files`
- `untracked_files`
- `snapshots`
- `receipt_hash`

Snapshots are base64 encoded. Paths must be safe repo-relative paths. Absolute paths and parent-directory escapes are invalid.

## RollbackResult

Required fields:

- `result_id`
- `boundary_ref`
- `run_id`
- `attempt_id`
- `attempted`
- `status`
- `recorded_at`
- `before`
- `after`
- `receipt_hash`

Status values:

- `restored`
- `not_required`
- `failed`
- `unavailable`

`failed` and `unavailable` require error evidence.

## Tools

Capture a boundary:

```bash
python3 tools/capture_rollback_boundary.py \
  --boundary-id rollback-boundary:example \
  --run-id governed-run:example \
  --attempt-id attempt:example
```

Record a result without mutating the workspace:

```bash
python3 tools/record_rollback_result.py \
  --boundary rollback-boundary.json \
  --result-id rollback-result:example
```

## Validation

Direct validation commands:

```bash
python3 tools/validate_rollback_receipts.py boundary tests/fixtures/receipts/rollback-boundary.valid.json
python3 tools/validate_rollback_receipts.py result tests/fixtures/receipts/rollback-result.valid.json
```

Negative fixtures:

- `rollback-boundary.path-escape.invalid.json`
- `rollback-result.failed-missing-error.invalid.json`

## Non-goals

This tranche does not implement mutating restore execution.

It does not decide whether rollback is required. That decision belongs to attempt admission, runtime action mapping, and authority state.

It does not replace runtime attempt receipts. It supplies evidence those receipts can cite.
