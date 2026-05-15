# Action proposal, admission handoff, runtime boundary, and runtime receipt contracts

This reference defines Agentplane ownership for the governed `Act -> Receipt` segment:

`AgentIntent -> ActionProposal -> PolicyDecision/ActionAdmission -> RuntimeBoundary -> RuntimeReceipt -> LearningEvent/Sociosphere update`

Agentplane consumes policy admission before runtime execution and emits runtime receipts after execution.

## Canonical loop position

`Observe -> Anchor -> Normalize -> Propose -> Explain -> Verify -> Govern -> Act -> Receipt -> Learn`

Agentplane owns the `Act -> Receipt` part and does not author policy rules.

## Contract map to Ontogenesis canonical objects

| Agentplane contract | Canonical object | Notes |
|---|---|---|
| `ActionProposal` | `ActionProposal` | Proposal carries action intent, expected effects, claim refs, and evidence refs before execution. |
| `ActionAdmission` | `ActionAdmission` | Admission record binds Policy Fabric decision output to Agentplane runtime boundary permission. |
| `RuntimeReceipt` | `RuntimeReceipt` | Runtime-side completion record emitted after admitted execution. |
| `policyDecision.policyDecisionArtifactRef` in `ActionAdmission` | `PolicyDecision` | Reuses `PolicyDecisionArtifact` (`schemas/policy-decision-artifact.schema.v0.1.json`) as policy decision evidence reference. |
| `claims[].claimRef` in `ActionProposal` | `Claim` | Claim refs capture action intent and expected effects. |
| `evidence[].evidenceRef` in `ActionProposal` | `Evidence` | Evidence refs attach supporting records without embedding raw payloads. |

## Runtime boundary handoff

`ActionAdmission.runtimeBoundary` defines the admitted runtime boundary:

- `nodeRef`
- `runtimeRef`
- `runtimeProfileRef`
- `sandboxProfileRef`

Execution is allowed only when admission status is `admitted`.

## Runtime receipt required fields

`RuntimeReceipt` requires:

- agent identity (`agentIdentity.agentId`, `agentIdentity.agentRef`)
- node/runtime identity (`runtimeIdentity.nodeRef`, `runtimeIdentity.runtimeRef`)
- sandbox/runtime profile (`runtimeProfile.runtimeProfileRef`, `runtimeProfile.sandboxProfileRef`)
- input/output hashes (`inputHash`, `outputHash`)
- logs reference (`logsRef`)
- policy decision reference (`policyDecisionRef`)
- start/end time (`startTime`, `endTime`)
- status (`status`)

## VectorCandidate usage rule

Prior-action similarity is advisory-only:

- use `ActionProposal.priorActionSimilarity.vectorCandidates[]` only as retrieval candidates;
- each candidate must remain `candidateOnly: true`;
- each candidate must keep `admissionAuthority: false`;
- policy re-evaluation remains mandatory (`reEvaluationRequired: true`) for every new action.

Similarity to a previously admitted action never authorizes a new action.

## Worked examples (fixtures)

### 1) GAIA bounded tile-manifest publish

Proposal -> Admission -> Runtime receipt:

- `fixtures/action-contracts/gaia-tile-manifest.proposal.v0.1.json`
- `fixtures/action-contracts/gaia-tile-manifest.admission.v0.1.json`
- `fixtures/action-contracts/gaia-tile-manifest.runtime-receipt.v0.1.json`

### 2) Agent-authored artifact review (admitted and denied records)

- `fixtures/action-contracts/artifact-review.proposal.v0.1.json`
- `fixtures/action-contracts/artifact-review.admission-admitted.v0.1.json`
- `fixtures/action-contracts/artifact-review.admission-denied.v0.1.json`

## Repository boundaries

- `sociosphere`: originates `AgentIntent`, consumes Agentplane runtime receipts for learning updates.
- `guardrail-fabric` / Policy Fabric: policy evaluation and decision authority (`PolicyDecision`), no execution ownership.
- `holmes`: reasoning/planning input refs; no runtime admission authority.
- `sherlock-search`: evidence retrieval refs used by proposals; no admission authority.
- `gaia-world-model`: world claims and bounded ingest/tile-manifest targets consumed by proposals.
- `agentplane`: admits/denies executable runtime work based on policy decision handoff, executes admitted actions, emits runtime receipts.

## Deterministic validation

Use:

```bash
python3 tools/validate_action_contracts.py
```

The validator checks schema headers, proposal/admission/receipt linkage, required runtime receipt fields, and `VectorCandidate` candidate-only posture.
