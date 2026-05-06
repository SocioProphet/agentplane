# ADR-0008: Route agent execution through Workspace Operation Plane contracts

Date: 2026-05-06  
Status: Accepted

## Context

Agent runs in agentplane historically wrote workspace artifacts (patches, reports,
metadata updates, terminal transcripts) as hidden side effects.  There was no
shared lifecycle record, no admission gate before activation, no ledger-facing
evidence, and no structured cancellation or compensation path.

The Operation Plane work (`SocioProphet/prophet-core-contracts#1`) introduces a
shared lifecycle for workspace mutations: `WorkspaceOperation`, `OperationTask`,
`OperationEvent`, `Artifact`, `DecisionCard`, and `PolicyGateRecord`.  Agent runs
are workspace mutations and should participate in this lifecycle.

Two routing models were considered:

1. **Opaque side-effect model** — agent runs write artifacts directly; the
   Operation Inspector observes results after the fact via separate reconciliation.
2. **Contract-first model** — every agent-initiated mutation must produce an
   `AgentOperationContract` record that carries the full lifecycle, authority,
   artifacts (in `pending-review` state), policy gate result, and event trail
   *before* any artifact is activated.

## Decision

The contract-first model is adopted.

All supported agent operation types — `agent.patch.propose`, `agent.report.create`,
`agent.metadata.fill`, `agent.failure.explain`, `agent.remediation.propose`, and
`agent.terminal.assist` — must emit an `AgentOperationContract` through
`scripts/emit_agent_operation_contract.py` (or the equivalent programmatic call)
instead of writing workspace artifacts as side effects.

Key invariants:

- **Admission gate**: agent-created artifacts are emitted with `admissionStatus:
  pending-review`.  They must not be activated without an explicit admission step
  by an authorised reviewer.
- **Delegated authority**: every contract records who the agent acts for
  (`authority.actingFor`), the explicit capability scopes granted, an optional
  resource budget, and the policy profile that governs the authority.
- **Idempotency and retry**: `lifecycle.idempotencyKey` is a stable key per
  attempt.  Repeated submissions with the same key must not duplicate effects.
  `lifecycle.retryable` and `lifecycle.retryCount` govern retry policy.
- **Cancellation evidence**: if the operation is cancelled, a `lifecycle.cancellation`
  record is emitted that identifies recoverable artifact refs.
- **Compensation**: if a compensation action is taken, `lifecycle.compensation`
  records the type and evidence ref.
- **Observable events**: `events[]` carries the full ordered event trail
  (`created`, `updated`, `retried`, `cancelled`, `artifact_emitted`,
  `gate_evaluated`, `completed`, `failed`, `compensation_started`,
  `compensation_completed`), making every run visible to the Operation Inspector.
- **Replay**: the `replayRef` field links to a `ReplayArtifact` enabling
  evidence-based replay of the operation.
- **Ledger**: the `ledgerRef` field links to the durable ledger record.

## Consequences

- **Positive:** Agent execution is observable and governable through the Operation
  Inspector.
- **Positive:** Agent-created artifacts can be reviewed and admitted before
  activation; no agent write happens outside an OperationContract.
- **Positive:** Retries respect idempotency keys and policy gates.
- **Positive:** Cancellations leave structured evidence and identify recoverable
  artifacts.
- **Positive:** The full event trail enables replay and audit.
- **Negative:** Every agent operation now requires an emission step; lightweight
  one-shot agent commands have more ceremony than before.
- **Negative:** The `AgentOperationContract` schema must be kept in sync with
  changes to the upstream `prophet-core-contracts` operation plane schema.

## References

- `SocioProphet/prophet-core-contracts#1`
- `SocioProphet/workspace-inventory#3`
- `SocioProphet/prophet-platform#376`
- `SocioProphet/policy-fabric#46`
- `schemas/agent-operation-contract.schema.v0.1.json`
- `scripts/emit_agent_operation_contract.py`
- `docs/integration/workspace-operation-plane.md`
