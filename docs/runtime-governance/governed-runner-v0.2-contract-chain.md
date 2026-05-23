# Governed Runner v0.2 Contract Chain

## Purpose

This document defines the synthetic governed-runner v0.2 contract-chain fixture.

The fixture proves that the cross-plane contracts compose without adding runtime execution.

## Fixture

```text
tests/fixtures/chains/governed-runner-v0.2-contract-chain.valid.json
```

## Validator

```text
tools/validate_governed_runner_v0_2_contract_chain.py
```

## Chain artifacts

The chain binds these surfaces:

- Agent Registry authority state;
- Guardrail Fabric safety handoff;
- AgentPlane governed run contract;
- AgentPlane attempt admission;
- AgentPlane synthetic verification receipt;
- AgentPlane budget settlement;
- AgentPlane run dossier.

## Required edges

The validator requires these edges:

```text
authority_state -> attempt_admission : authority_input
safety_handoff -> attempt_admission : safety_input
governed_run_contract -> attempt_admission : contract_input
attempt_admission -> verification_receipt : admission_required
verification_receipt -> budget_settlement : settlement_after_result
attempt_admission -> run_dossier : dossier_summarizes
budget_settlement -> run_dossier : dossier_summarizes
```

## Invariants

The validator enforces:

- Agent Registry owns authority state;
- Guardrail Fabric owns safety handoff;
- AgentPlane owns governed-runner evidence;
- safety handoff preserves `authoritative_safety_owner`;
- safety handoff is pass/allow;
- attempt admission is admit;
- verification receipt is synthetic;
- verification receipt is allowlisted;
- verification receipt has network mode off;
- verification receipt has mutation mode none;
- budget settlement does not hide overrun;
- run dossier is ready;
- all blocked capabilities remain blocked.

## Validation

```bash
make validate-governed-runner-v0-2-contract-chain
```

or directly:

```bash
python3 tools/validate_governed_runner_v0_2_contract_chain.py \
  tests/fixtures/chains/governed-runner-v0.2-contract-chain.valid.json
```

## Boundary

This is a contract-chain fixture only.

It does not add:

- real verifier runner;
- shell passthrough;
- arbitrary command input;
- network activity;
- workspace mutation;
- provider invocation;
- authority update;
- recovery action;
- provider-backed budget integration.
