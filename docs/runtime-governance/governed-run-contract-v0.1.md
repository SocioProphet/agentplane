# GovernedRunContract v0.1

## Purpose

`GovernedRunContract` is AgentPlane's canonical executable run input object for governed runtime admission.

It is the first product-facing contract for the SCOPE-D Governed Runner lane: a task cannot be admitted for effectful runtime execution until the run contract binds objective, workspace, repo boundary, agent identity, authority grant, policy bundle, TrustOps gate policy, budget, verifier plan, network posture, rollback requirement, and receipt requirements.

## Boundary

AgentPlane owns this contract because AgentPlane owns governed execution, attempt admission, runtime evidence, replay material, and receipt sealing.

Related planes:

- `guardrail-fabric` owns safety preflight and TrustOps runtime action mapping.
- `agent-registry` owns current authority state and authority grants.
- `sociosphere` coordinates cross-repo workflow state.
- `SCOPE-D` consumes generated run evidence and dossiers for product/operator workflows.

## Required fields

- `run_id`
- `objective`
- `workspace_ref`
- `repo_root`
- `agent_ref`
- `authority_grant_ref`
- `policy_bundle_ref`
- `trustops_gate_policy_ref`
- `budget`
- `verification_plan`
- `allowed_paths`
- `denied_paths`
- `network_mode`
- `execution_profile`
- `mutation_mode`
- `rollback_required`
- `receipt_requirements`

## Budget

Budget is mandatory and includes:

- `max_usd`
- `soft_limit_usd`
- `max_iterations`
- `max_tokens`

`soft_limit_usd` must be less than or equal to `max_usd`.

## Verification plan

Mutation runs require a non-empty verification plan.

Each verification step includes:

- `command`
- `kind = lint | typecheck | test | security | custom`
- optional `required`

Destructive verifier commands are rejected by the validator as an early contract-level guard. The full command safety analysis belongs to `guardrail-fabric` safety preflight.

## Path safety

`repo_root`, `allowed_paths`, and `denied_paths` must be safe relative paths or patterns.

Rejected forms include:

- absolute paths
- `..`
- `../...`
- patterns containing `/../`

`allowed_paths` must be non-empty.

## Network posture

`network_mode` is one of:

- `off`
- `allowlisted`
- `open`

`open` is schema-valid but should only be admitted when policy grants it. The safety preflight layer enforces runtime network posture.

## Rollback

Mutation runs require `rollback_required=true`.

Rollback boundary and rollback outcome receipts are optional at schema level but required by the governed-runner acceptance path when mutation is enabled.

## Receipt requirements

The following receipt requirements must be true:

- `safety_preflight`
- `attempt_admission`
- `runtime_attempt`
- `verification_result`
- `run_dossier`

Rollback receipts are included as explicit fields:

- `rollback_boundary`
- `rollback_outcome`

## Validation

```bash
make validate-governed-run-contract
```

The validation target checks:

- schema JSON parses
- valid fixture passes
- missing policy bundle fails
- missing budget fails
- verifier-less mutation fails
- absolute/unsafe path fails
- missing authority grant fails

## Non-goals

This contract does not execute a run.

It does not decide admission by itself. Attempt admission will consume this contract together with:

- TrustOps safety preflight decision
- Agent Registry authority state
- budget estimate
- TrustOps runtime action mapping

It does not define CLI or MCP shape. Those surfaces should accept or produce this contract, not replace it.
