# Runtime governance integration plan

> **Status: partially implemented.**  
> The first runtime enforcement surface is now live: `scripts/validate_bundle.py` evaluates the imported `compiled_policy_bundle_v3.json` through `scripts/evaluate_control_matrix_gate.py` and emits a `ControlGateArtifact` before execution proceeds. The imported file is currently a policy-engine execution slice of the broader control matrix.  
> Monitor and generated-test lanes remain planned follow-on surfaces.  
> See [policy/imports/control-matrix/README.md](../../policy/imports/control-matrix/README.md) for the current import state.

This document defines the first expected binding points for the imported control bundle.

## Initial enforcement surfaces

1. Policy gate
   - import the compiled policy bundle
   - derive a narrow execution context from bundle policy (`lane`, `humanGateRequired`, optional control-matrix overrides)
   - evaluate `policy_engine` rows and fail closed when no exact row matches
   - emit `control-gate-artifact.json` for every evaluated bundle

2. Monitor lane
   - ingest generated monitor bundle definitions
   - attach monitor health and stale-review checks
   - reconcile incidents back to row IDs

3. Generated test lane
   - ingest generated test bundle definitions
   - run high-risk row checks on integration and release paths

## Evidence expectations

Runtime actions should emit:

- row id
- bundle version
- decision
- evidence references
- incident linkage when applicable
- exception linkage when applicable

## Control loop

The runtime lane should eventually close the loop:

monitor breach -> incident -> change proposal -> bundle regeneration -> review -> redeploy
