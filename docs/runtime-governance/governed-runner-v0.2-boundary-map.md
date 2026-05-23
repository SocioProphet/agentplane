# Governed Runner v0.2 Boundary Map

Status: boundary map after v0.1 read-only release and v0.2 contract tranches

Owning repo: `SocioProphet/agentplane`

## Purpose

This document records the governed-runner v0.2 boundary map after the cross-plane contract tranches landed.

It is the canonical map for what is implemented as a contract, what is owned by adjacent planes, what remains evidence-only, and what must not be implemented without a separate policy-gated tranche.

## Current cross-plane contracts

| Concern | Owning repo | Artifact / surface | Status |
|---|---|---|---|
| Authority lookup | `SocioProphet/agent-registry` | `tools/authority_state_lookup.py` returning `AgentAuthorityCurrentState` | merged in `agent-registry#39` |
| Safety handoff | `SocioProphet/guardrail-fabric` | `TrustOpsPreflightHandoff v0.1` | merged in `guardrail-fabric#29` |
| Attempt admission | `SocioProphet/agentplane` | `AttemptAdmissionReceipt v0.1` | merged |
| Budget settlement | `SocioProphet/agentplane` | `BudgetSettlementReceipt v0.1` | merged in `agentplane#209` |
| Verifier result evidence | `SocioProphet/agentplane` | `VerificationExecutionReceipt v0.1` | merged in `agentplane#210` |
| Integrity evidence | `SocioProphet/agentplane` | `IntegrityEvidenceRequest v0.1` and `IntegrityEvidenceResult v0.1` | merged in `agentplane#211` |
| Product facade | `SocioProphet/prophet-cli` | `prophet governed-runner ... -> sp-run ...` | merged |
| Install path | `SocioProphet/homebrew-prophet` | `brew install prophet-cli agentplane` | merged |

## Ownership rules

### Guardrail Fabric owns safety semantics

AgentPlane may consume Guardrail Fabric handoff records. AgentPlane must not reinterpret safety outcomes, lower runtime action severity, invent missing evidence references, or collapse deny-like states into warning states.

### Agent Registry owns authority state

AgentPlane may consume `AgentAuthorityCurrentState`. AgentPlane must not compute, mutate, or restore authority state from raw TrustOps receipts.

### AgentPlane owns governed-runner evidence contracts

AgentPlane owns governed-runner contracts, admission receipts, dossiers, evidence receipts, smoke evidence, inspection, and `sp-run` read-only surfaces.

### prophet-cli owns command names only

`prophet-cli` remains a facade. It must delegate governed-runner behavior to `sp-run` and must not duplicate AgentPlane implementation.

## Contract boundaries

### Authority-state lookup

Authority lookup is read-only.

Allowed output:

```text
AgentAuthorityCurrentState
```

Non-goals:

```text
authority mutation
restoration approval
raw receipt to authority-state derivation
AgentPlane admission emission
runtime execution
```

### Preflight handoff

Guardrail Fabric handoff provides AgentPlane-consumable safety projection:

```text
outcome
runtime_action
authoritative_safety_owner
handoff_ref
```

Required invariants:

```text
outcome maps monotonically to runtime_action
rollback cannot degrade to warn
quarantine preserves evidence refs and gate ids
AgentPlane projection preserves authoritative_safety_owner and handoff_ref
```

### Budget settlement receipt

Budget settlement separates:

```text
estimate != admission != settlement
```

`BudgetSettlementReceipt` records actuals and overrun status. It does not authorize execution and must not be used as admission authority.

### Verification execution receipt

`VerificationExecutionReceipt` is a receipt boundary for verifier-result evidence.

A valid v0.1 receipt requires:

```text
admission_decision = admit
preflight_outcome = pass
runtime_action = allow
authority is not suspended or revoked
verifier command is allowlisted
network_mode = off
mutation_mode = none
```

This contract does not add a runner.

### Integrity evidence contract

`IntegrityEvidenceRequest` and `IntegrityEvidenceResult` record safe-root and digest evidence.

Required invariants:

```text
admission_ref points to AttemptAdmissionReceipt
authority_status is not suspended or revoked
paths remain under declared safe root
digests are sha256-bound
matches_expected equals observed_digest == expected_digest
recorded status requires matching observed and expected digests
```

This contract is evidence-only.

## Explicitly blocked until separate policy-gated tranche

The following remain blocked:

- verifier-result production implementation;
- shell or arbitrary command execution;
- workspace mutation;
- integrity evidence production from live files;
- recovery action implementation;
- rollback restore implementation;
- authority mutation;
- restoration approval;
- budget settlement integration with provider APIs;
- live token metering;
- provider invocation;
- network activity for a governed run;
- background daemon behavior.

## Required next implementation issue before runtime work

Before any runtime-producing command is implemented, open a new issue with explicit acceptance criteria for a synthetic, non-mutating verifier-result producer.

That issue must require:

- no shell passthrough;
- no arbitrary command input;
- fixture-only verifier plan;
- network mode off;
- mutation mode none;
- authority lookup consumed from Agent Registry output;
- safety handoff consumed from Guardrail Fabric output;
- `AttemptAdmissionReceipt` must admit;
- emitted `VerificationExecutionReceipt` must validate;
- no budget settlement integration in the first implementation tranche.

## Stopping rule

If a proposed implementation requires any of the blocked capabilities above, stop and create a separate design issue first.

Do not expand `sp-run` from read-only/evidence-generation into runtime behavior without an accepted policy-gated implementation issue and negative fixtures.
