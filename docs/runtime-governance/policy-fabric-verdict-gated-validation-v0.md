# Policy Fabric verdict-gated validation v0

## Status

Interim implementation note.

## What exists now

The branch now contains an interim wrapper entry point:

- `scripts/validate_bundle_with_policy_fabric_gate.py`

This wrapper:
1. runs the existing `scripts/validate_bundle.py`
2. optionally consumes a Policy Fabric verdict envelope
3. emits `policy-fabric-verdict-gate-artifact.json`
4. fails closed when the envelope is required and missing, or when `promote = false`

## Why this exists

This is the safest first implementation tranche for the seam because it adds executable behavior without patching the core validator in-place.

That keeps the execution-side change reviewable while still giving Agentplane a real governed admission path for verdict consumption.

## Invocation

Example:

```bash
python3 scripts/validate_bundle_with_policy_fabric_gate.py \
  path/to/bundle.json \
  --verdict-envelope path/to/policy-fabric-verdict-envelope.json \
  --require-verdict-envelope
```

Alternatively, the verdict envelope path may be supplied through:

```bash
export POLICY_FABRIC_VERDICT_ENVELOPE=path/to/policy-fabric-verdict-envelope.json
```

## Follow-on

A later tranche may inline this behavior directly into `scripts/validate_bundle.py` once the seam is stable and the temporary probe schema file has been removed.
