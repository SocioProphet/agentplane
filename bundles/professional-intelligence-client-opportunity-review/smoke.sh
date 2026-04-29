#!/usr/bin/env bash
set -euo pipefail

out_dir="${AGENTPLANE_ARTIFACT_DIR:-./artifacts/professional-intelligence-client-opportunity-review}"
mkdir -p "${out_dir}"

started_at="$(date -Iseconds)"

cat > "${out_dir}/professional-intelligence-workflow-step.json" <<JSON
{
  "kind": "ProfessionalIntelligenceWorkflowStep",
  "schemaVersion": "v0.1",
  "workflowId": "client-opportunity-review",
  "stepId": "review-packet",
  "capability": "agent-fabric",
  "workroomRef": "workroom://workroom-demo-0001",
  "contextRefs": [
    "context-pack://pi-demo-0001",
    "entity://organization/org-demo-0001"
  ],
  "policyDecisionRefs": [
    "policy-decision://ppd-review-0001"
  ],
  "obligationRefs": [
    "obligation://obl-ai-use-demo-0001"
  ],
  "result": "requires_review",
  "startedAt": "${started_at}",
  "endedAt": "$(date -Iseconds)"
}
JSON

cat > "${out_dir}/run-artifact.json" <<JSON
{
  "kind": "RunArtifact",
  "bundle": "professional-intelligence-client-opportunity-review@0.1.0",
  "lane": "staging",
  "backend": "record-only",
  "executedIn": "agentplane-bundle-smoke",
  "startedAt": "${started_at}",
  "endedAt": "$(date -Iseconds)",
  "result": "pass",
  "evidenceRefs": [
    "${out_dir}/professional-intelligence-workflow-step.json"
  ]
}
JSON

cat > "${out_dir}/replay-artifact.json" <<JSON
{
  "kind": "ReplayArtifact",
  "bundle": "professional-intelligence-client-opportunity-review@0.1.0",
  "inputs": [
    "bundle.json",
    "smoke.sh",
    "policy-decision://ppd-review-0001",
    "obligation://obl-ai-use-demo-0001",
    "workroom://workroom-demo-0001"
  ],
  "expectedOutputs": [
    "professional-intelligence-workflow-step.json",
    "run-artifact.json"
  ],
  "createdAt": "$(date -Iseconds)"
}
JSON

echo "Professional Intelligence workflow bundle smoke emitted artifacts under ${out_dir}"
