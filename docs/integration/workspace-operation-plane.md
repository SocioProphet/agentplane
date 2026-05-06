# Integration guide: Workspace Operation Plane → agentplane

## Status

Accepted (see [ADR-0008](../adr/0008-agent-operation-plane-routing.md)).

## Purpose

This guide explains how to route agent execution through Workspace Operation Plane
contracts so that every agent-initiated workspace mutation is observable,
governable, and auditable.

## Why this matters

Without Operation Plane routing, agent writes are hidden side effects.  There is no
shared lifecycle record, no admission gate before artifact activation, and no
structured evidence for the Operation Inspector, replay, or ledger.

With Operation Plane routing:

- Every agent-created artifact starts in `admissionStatus: pending-review` and
  cannot be activated without an explicit admission step.
- Agent run events are visible to the Operation Inspector via the `events[]` trail.
- Retries are idempotent and governed by policy gates.
- Cancellation leaves structured evidence and identifies recoverable artifacts.
- Replay is possible through the `replayRef` → `ReplayArtifact` chain.

## Supported agent operation types

| Operation type | Description |
|---|---|
| `agent.patch.propose` | Agent proposes a code patch for review and admission. |
| `agent.report.create` | Agent creates a report artifact. |
| `agent.metadata.fill` | Agent fills metadata fields in workspace objects. |
| `agent.failure.explain` | Agent explains an observed failure. |
| `agent.remediation.propose` | Agent proposes a remediation action. |
| `agent.terminal.assist` | Agent assists with a terminal operation. |

## Contract structure

An `AgentOperationContract` carries:

| Field | Role |
|---|---|
| `operationId` | Unique stable identifier for idempotency and ledger correlation. |
| `operationType` | One of the six supported agent operation types. |
| `authority` | Delegated authority: who the agent acts for, scopes, budget, policy profile, audit level. |
| `lifecycle` | Status, idempotency key, retry count, cancellation record, compensation record. |
| `tasks[]` | `OperationTask` records: the individual units of work. |
| `events[]` | `OperationEvent` records: the full ordered lifecycle event trail. |
| `artifacts[]` | Agent-created artifacts in `pending-review` state until admitted. |
| `decisionCard` | `DecisionCard`: what the agent decided and why. |
| `policyGate` | `PolicyGateRecord`: the policy gate evaluation result. |
| `replayRef` | Link to the `ReplayArtifact` for evidence-based replay. |
| `ledgerRef` | Link to the durable ledger record. |

## Step-by-step usage

### 1. Validate the bundle

```bash
python3 scripts/validate_bundle.py path/to/bundle.json
```

### 2. Run the agent operation

Execute your agent command.  The agent must not write workspace artifacts directly.

### 3. Emit the operation contract

After the agent run completes (or when updating lifecycle state), emit the contract:

```bash
python3 scripts/emit_agent_operation_contract.py path/to/bundle.json \
    --operation-type agent.patch.propose \
    --operation-id op-20260506-001 \
    --acting-for user:octocat \
    --scope workspace:write \
    --scope pr:propose \
    --scope artifacts:emit \
    --status completed \
    --artifact-type patch \
    --artifact-ref artifacts/patch/my-change.diff \
    --policy-ref policy://agentplane/default-patch-propose \
    --policy-result allow \
    --decision "Propose patch for issue #1" \
    --rationale "Issue requires operation plane routing; patch adds the contract schema and emit script."
```

This writes `agent-operation-contract.json` to `bundle.spec.artifacts.outDir`.

### 4. Emit the run artifact

```bash
python3 scripts/emit_run_artifact.py path/to/bundle.json my-executor 0
```

### 5. Emit the replay artifact

```bash
python3 scripts/emit_replay_artifact.py path/to/bundle.json my-executor --bundle-rev "$GIT_SHA"
```

### 6. Admit or reject artifacts

An authorised reviewer inspects the `artifacts[]` array in the contract and
explicitly sets `admissionStatus` to `admitted` or `rejected` before any artifact
is activated in the workspace.  Agents must not perform this step themselves.

## Idempotency and retries

The `lifecycle.idempotencyKey` is derived as `{operationId}/attempt-{retryCount+1}`.
If an operation fails and is retried:

- Pass `--retry-count <n>` where `n` is the previous attempt count.
- The idempotency key changes automatically, preventing duplicate effects.
- The policy gate is re-evaluated on each retry.

## Cancellation

When an operation is cancelled before completion, emit the contract with
`--status cancelled`.  The `lifecycle.cancellation` block (populated programmatically
or by the runtime) records:

- `cancelledAt` — when the cancellation occurred.
- `cancelledBy` — who or what triggered the cancellation.
- `reason` — why the operation was cancelled.
- `recoverableArtifactRefs` — refs to any artifacts that can still be recovered.

## Compensation

When a completed operation needs to be rolled back, emit an updated contract with
`--status compensating` and populate `lifecycle.compensation` with:

- `compensatedAt` — when compensation was initiated.
- `compensationType` — one of `rollback`, `undo-patch`, `archive-artifacts`, `manual-review`.
- `evidenceRef` — reference to the compensation evidence artifact.

## Non-goals

- `agentplane` does not re-scan the workspace for agent side effects.  Operations
  that bypass the contract path are not governed.
- Artifact admission is not performed by agentplane; it is the responsibility of
  an authorised reviewer in the appropriate admission tool.
- This guide does not cover the upstream `prophet-core-contracts` operation plane
  schema; see `SocioProphet/prophet-core-contracts#1` for that specification.

## References

- [ADR-0008: Route agent execution through Workspace Operation Plane contracts](../adr/0008-agent-operation-plane-routing.md)
- [schemas/agent-operation-contract.schema.v0.1.json](../../schemas/agent-operation-contract.schema.v0.1.json)
- [scripts/emit_agent_operation_contract.py](../../scripts/emit_agent_operation_contract.py)
- [examples/agent-operation-contract.example.json](../../examples/agent-operation-contract.example.json)
- `SocioProphet/prophet-core-contracts#1`
- `SocioProphet/workspace-inventory#3`
