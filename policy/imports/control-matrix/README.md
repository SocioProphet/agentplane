# Control matrix import lane

This directory holds imported Agentic Control Matrix bundles for `agentplane`.

## Source of truth

The canonical standards package lives in:

- `SocioProphet/socioprophet-standards-storage`

`agentplane` is the consumer/runtime lane. It should import and pin released bundle versions from the standards repository rather than redefining the ontology locally.

## Current state

The import lane now contains:

- manifest and upstream pin metadata
- imported `compiled_policy_bundle_v3.json`
- a first live policy-gate binding in `scripts/validate_bundle.py`

The validator now emits `control-gate-artifact.json` and fails closed when no exact `policy_engine` row matches the derived bundle execution context. The vendored `compiled_policy_bundle_v3.json` is the first executable policy-engine slice, not yet the full multi-surface bundle release.

## Remaining follow-on

- bind the generated monitor bundle to runtime monitor health checks
- bind the generated test bundle into integration / release gates
- move from commit-pin semantics to tagged release or release-asset pinning
