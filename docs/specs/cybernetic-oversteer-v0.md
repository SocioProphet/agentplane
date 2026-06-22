# Cybernetic Oversteer v0

## Purpose

Defines oversteer as a first-class governance condition in the tensegrity runtime. Oversteer occurs when the execution system is self-correcting faster than evidence-gathering can validate. It signals that tension members are under strain: policy is reversing, evidence is not accumulating, or the actor is outrunning its capability radius.

## Oversteer Indicators

Each indicator maps to a pattern in the execution record or governance signal stream.

| Indicator                     | Description                                                                                      | Tension Member Under Strain    |
|-------------------------------|--------------------------------------------------------------------------------------------------|-------------------------------|
| repeated_reversals            | The same decision (approve/deny, dispatch/block) is reversed three or more times in a session   | Policy                        |
| patch_churn                   | More than N patches to the same artifact within a bounded time window without advancing the evidence chain | Provenance, Evidence |
| issue_churn                   | Issues are opened and closed on the same scope without resolution propagating to execution artifacts | Evidence, Audit |
| branch_churn                  | More than N branch create/delete cycles on the same base without a merged artifact              | Repo, Provenance              |
| oscillating_decisions         | Policy decisions flip between allow and deny on the same request profile without new evidence   | Policy                        |
| policy_flip_flops             | A policy decision is overridden, reinstated, and overridden again within one run capsule        | Policy                        |
| repeated_failed_validations   | The same validation check fails three or more consecutive times without a new evidence artifact | Tests, Evidence               |
| excessive_retry_no_evidence   | Retries exceed threshold with no new evidence_refs added to the run capsule                     | Evidence, Replay              |
| rapid_radius_escalation       | Actor capability radius jumps two or more levels without intermediate evidence and policy gates | Capability Grants             |
| tension_member_gap            | A required tension member (e.g., replay_ref) is absent from a mutation-class action            | Varies                        |

## Detection Contract

Oversteer indicators are emitted as `OvensteerIndicator` fields in the `OversteerGovernanceSignal` artifact (see `examples/governance/oversteer-indicators.example.json`). They do not block execution directly but:

1. Are emitted to HellGraph/Prophet Core as evidence.
2. Trigger a `delivery_excellence_signal_ref` with a degraded score.
3. Elevate the next policy decision request to `escalate` if two or more indicators fire simultaneously.
4. Are included in the RationalGRL trace as softgoal degradation events.

## Oversteer vs. Error

An error is a single-point failure with a clear revocation path. Oversteer is a systemic pattern. Errors resolve through repair and evidence. Oversteer resolves through tension member reinforcement: adding evidence, slowing radius expansion, or requiring human authority at R4/R5.

## Non-Claims

- This spec does not define the thresholds N for churn indicators; those are set by PolicyFabric configuration per org and repo.
- This spec does not prescribe automatic execution halt; that is a policy gate decision.
