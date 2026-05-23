# Semantic Activation Context Divergence v0

## Purpose

This fixture proves a boundary case for `SemanticActivationReceipt v0.1`:

```text
same activation_bundle_hash != same admission result
```

A semantic activation bundle can be admitted under one executor/policy context and fail closed under another. The activation input is stable, but the runtime context is not equivalent.

## Why this exists

The governed-runner and semantic-activation surfaces must not let operators infer equivalence from the activation bundle alone.

The admission boundary includes:

- activation bundle hash;
- validator bundle;
- executor id and version;
- graph snapshot;
- policy bundle;
- policy decision;
- replay artifact;
- evidence status;
- fail-closed reason when applicable.

Without a paired public fixture, future contributors could read the schema and still miss the boundary case.

## Fixtures

Admitted context:

```text
tests/fixtures/receipts/semantic-activation-receipt.divergence-admitted.valid.json
```

Fail-closed context:

```text
tests/fixtures/receipts/semantic-activation-receipt.divergence-fail-closed.valid.json
```

Chain proof:

```text
tests/fixtures/receipts/semantic-activation-context-divergence.chain.json
```

## Invariant

The paired receipts must share:

```text
activation_bundle_hash
```

The paired receipts must differ in at least:

```text
validator_bundle_ref
executor_version
graph_snapshot_id
policy_bundle_id
policy_decision_ref
replay_artifact_ref
```

The admitted receipt must have:

```text
admission_decision = admitted
evidence_status = complete
```

The fail-closed receipt must have:

```text
admission_decision = fail-closed
fail_closed_reason present
```

## Validation

Run the pair validator:

```bash
python3 tools/validate_semantic_activation_context_divergence.py \
  tests/fixtures/receipts/semantic-activation-context-divergence.chain.json
```

Or run the existing semantic activation target:

```bash
make validate-semantic-activation-receipt
```

## Operator boundary

This proof fixture records four operator-facing constraints:

```text
same_activation_bundle_is_not_same_runtime_context = true
fail_closed_context_requires_fail_closed_reason = true
replay_artifacts_must_remain_distinguishable = true
policy_context_is_admission_boundary = true
```

## Non-goals

This fixture does not add:

- live agent execution;
- verifier execution;
- governed workspace mutation;
- rollback restoration;
- authority mutation;
- budget settlement;
- provider invocation;
- network activity.

It is a public evidence fixture and invariant test for the semantic-activation admission boundary.
