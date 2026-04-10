#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-./artifacts/example-assessment-vendor-acme}"
mkdir -p "$OUT_DIR"

cat > "$OUT_DIR/run-artifact.json" <<JSON
{
  "kind": "RunArtifact",
  "bundle": "example-assessment-vendor-acme@0.1.0",
  "startedAt": "$(date -Iseconds)",
  "inputs": { "subjectId": "vendor:acme-cloud", "frameworkId": "nist-800-53-rev5" },
  "toolCalls": [],
  "outputs": { "note": "assessment smoke stub" },
  "environment": { "note": "stub - will later include runtime, executor, and module hashes" }
}
JSON

cat > "$OUT_DIR/control-evaluations.json" <<JSON
[
  {
    "evaluation_id": "eval_nist_ac_2_001",
    "row_id": "ac-2-account-management",
    "status": "partial",
    "decision": "require_approval"
  }
]
JSON

cat > "$OUT_DIR/findings.json" <<JSON
[
  {
    "finding_id": "finding_nist_ac_2_001",
    "evaluation_ref": "eval_nist_ac_2_001",
    "severity": "high",
    "disposition": "open"
  }
]
JSON

cat > "$OUT_DIR/assessment-receipt.json" <<JSON
{
  "receipt_id": "receipt_vendor_acme_assessment_001",
  "trace_id": "trace_vendor_acme_assessment_001",
  "evaluation_refs": ["eval_nist_ac_2_001"],
  "finding_refs": ["finding_nist_ac_2_001"],
  "replay": { "manifest_ref": "replay://vendor-acme-assessment/001", "replayable": true },
  "sealed_at": "$(date -Iseconds)"
}
JSON

echo "[smoke] wrote assessment artifacts to $OUT_DIR"
