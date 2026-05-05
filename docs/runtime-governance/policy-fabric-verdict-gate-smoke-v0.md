# Policy Fabric verdict gate smoke v0

## Status

Smoke guide.

## Purpose

This document gives the minimum positive and negative smoke path for the interim Policy Fabric verdict-gated validation wrapper.

The wrapper is:

- `scripts/validate_bundle_with_policy_fabric_gate.py`

The example bundle is:

- `bundles/example-agent/bundle.json`

The smoke verdict envelopes are:

- `examples/policy-fabric-verdict-envelope.allow.example.json`
- `examples/policy-fabric-verdict-envelope.deny.example.json`

## Positive smoke path

The allow fixture should pass after normal bundle validation succeeds:

```bash
python3 scripts/validate_bundle_with_policy_fabric_gate.py \
  bundles/example-agent/bundle.json \
  --verdict-envelope examples/policy-fabric-verdict-envelope.allow.example.json \
  --require-verdict-envelope
```

Expected result:

- command exits `0`
- `artifacts/example-agent/policy-fabric-verdict-gate-artifact.json` is emitted
- gate artifact contains `result = allow`

## Negative smoke path

The deny fixture should fail closed after normal bundle validation succeeds:

```bash
python3 scripts/validate_bundle_with_policy_fabric_gate.py \
  bundles/example-agent/bundle.json \
  --verdict-envelope examples/policy-fabric-verdict-envelope.deny.example.json \
  --require-verdict-envelope
```

Expected result:

- command exits nonzero
- `artifacts/example-agent/policy-fabric-verdict-gate-artifact.json` is emitted
- gate artifact contains `result = deny`

## Missing-envelope smoke path

When the wrapper is invoked with `--require-verdict-envelope`, missing verdict material should fail closed:

```bash
python3 scripts/validate_bundle_with_policy_fabric_gate.py \
  bundles/example-agent/bundle.json \
  --require-verdict-envelope
```

Expected result:

- command exits nonzero
- stderr explains that the verdict envelope is required but not provided

## Why this matters

This smoke guide proves the seam has the minimum governed execution behavior:

1. normal bundle validation still runs first;
2. Policy Fabric verdict material can allow execution admission;
3. Policy Fabric verdict material can deny execution admission;
4. missing required verdict material fails closed.

## Follow-on

A later implementation tranche should convert this smoke guide into a repo-native test script once the cleanup PR removing the temporary probe schema has merged.
