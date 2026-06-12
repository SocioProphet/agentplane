# Rollback Restore — Design Contract v0

## What restore can mutate

Restore is limited to **files and directories explicitly listed** in `restore_target_paths`, subject to:

1. **safe_root boundary**: Every path in `restore_target_paths` must be a child of `safe_root`. Paths outside this prefix are rejected at validation time as a path escape.
2. **path_allowlist**: When present, every `restore_target_paths` entry must also appear in `path_allowlist`. The allowlist is a further restriction, never an expansion.
3. **RollbackBoundary scope**: Restore only applies within the declared `rollback_boundary_ref`. Cross-repo restore and restore outside the boundary are not admitted.
4. **No arbitrary file mutation**: Restore does not grant write access to paths not named in the request. It restores declared state; it does not apply diffs or execute code.

## Evidence conditions required for restore

Every `RollbackRestoreRequest` must carry:

| Field | Requirement |
|---|---|
| `rollback_boundary_ref` | Existing boundary artifact declaring the restore scope |
| `admission_ref` | An admitted `RestoreAdmission` artifact approving this request |
| `authority_ref` + `authority_state` | Non-anonymous authority in `active` state |
| `before_digest` | SHA-256 digest of the pre-restore state (sha256:<64 hex chars>) |
| `policy_decision_ref` | Policy decision authorising this restore |
| `non_claims` | At least one non-claim scoping what this restore does not assert |

Every `RollbackRestoreReceipt` for a `completed` restore must carry:

| Field | Requirement |
|---|---|
| `before_digest` + `before_digest_verified: true` | Pre-restore state was verified against the request digest |
| `after_digest` + `after_digest_verified: true` | Post-restore state was verified against `expected_after_digest` |

A receipt with `restore_status: completed` and `before_digest_verified: false` or `after_digest_verified: false` is rejected — unverified digests indicate a mismatch or incomplete evidence chain and cannot be treated as a successful restore.

## Authority states

| State | Restore admitted? |
|---|---|
| `active` | Yes |
| `suspended` | No — rejected at validation |
| `revoked` | No — rejected at validation |

## Non-goals (preserved from issue #206)

- No restore implementation in this design — schema and evidence contract only.
- No arbitrary file mutation outside named paths.
- No cross-repo restore.
- No restore outside `safe_root`.
- No authority update through this schema.
- No budget settlement.
- No live agent execution.

## Integration points

- `rollback_boundary_ref` → existing `RollbackBoundary` in governed-runner v0.2 contract chain.
- `admission_ref` → `RestoreAdmission` (to be defined in implementation PR).
- `policy_decision_ref` → policy-fabric `PolicyDecisionArtifact`.
- Receipts feed into HellGraph evidence graph as evidence nodes.
