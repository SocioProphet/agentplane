# ExecutionEnvelope runtime contract

Agentplane consumes an `ExecutionEnvelope` supplied by the workflow controller / trust plane.

Required envelope refs by trust mode:

- `attestationMode = none` -> attestation refs optional
- `attestationMode = subject` -> `attestationBundleRef` required for subject
- `attestationMode = executor` -> `attestationBundleRef` required for executor
- `attestationMode = subject+executor` -> subject + executor attestation coverage required

- `grantMode = none` -> `grantRef` optional
- `grantMode = runtime_optional` -> `grantRef` optional but used when present
- `grantMode = runtime_required` -> `grantRef` required

- `policyDecisionRequired = true` -> `policyDecisionRef` required

The envelope also carries:
- `runId`
- `stepId`
- `subject`
- `inputRefs`
- `inputDigest`
- optional `quorumProofRef`
