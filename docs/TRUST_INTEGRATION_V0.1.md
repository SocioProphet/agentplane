# Trust integration v0.1

This scaffold prepares `agentplane` to consume the workflow-kernel execution contract defined in
`sociosphere/protocol/agentic-workbench/v1/` and the canonical trust objects from
`mcp-a2a-zero-trust`.

## Static vs dynamic split

### Static bundle
The bundle declares trust requirements:

- `spec.trust.attestationMode`
- `spec.trust.grantMode`
- `spec.trust.policyDecisionRequired`
- `spec.trust.ledgerMode`
- `spec.trust.redactionProfileRef`

### Dynamic execution envelope
Runtime authorization is carried in a separate `ExecutionEnvelope` object and must include refs to:

- `AttestationBundle`
- `PolicyDecision`
- `Grant`
- optional `QuorumProof`

## Fail-closed rules

If `spec.trust.grantMode = runtime_required`, execution MUST fail closed when no valid `grantRef`
is present in the envelope.

If `spec.trust.attestationMode != none`, execution MUST fail closed when required attestation refs
are absent.

If `spec.trust.ledgerMode = required`, execution MUST fail closed when receipts cannot be linked
to ledger refs or payload hashes.

## Evidence receipts

Agentplane should emit receipts for:
- validate
- place
- run / dispatch
- result
- replay
- compensation

Each receipt should carry:
- `runId`
- `stepId`
- `phase`
- `payloadHash`
- `outputHash` (if any)
- `ledgerEventRef` (or stable payload-hash linkage)

## Projection source

Static bundle projections are compiled from:
`sociosphere/protocol/agentic-workbench/v1/WorkflowSpec`

Runtime authorization is supplied by:
`mcp-a2a-zero-trust`
