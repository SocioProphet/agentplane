# state-drift-lab

Benchmark recipe bundle for canonical-state recovery, projection drift explanation, backend lag classification, and sparse-observation workflow regimes.

## Purpose

This bundle is the first scenario family for the State / Projection / Observation Evidence Kernel.
It exists to force the reconciler to survive the exact classes of contradictions that routinely appear in repo-native agent workflows:

- stale derived projections
- backend lag
- hidden `branch_pr` progress
- missing verification artifacts
- conflicting authority surfaces
- malformed rendered bodies

## Notes

This staging copy is a proposal surface.
The real execution logic should live in AgentPlane core, with this recipe acting as the signed catalog and failure museum.

## Included here

- draft manifest
- one representative scenario
- initial scorecard metrics
- draft catalog entry

A fuller bundle with additional scenarios and a tarball packaging step has already been prepared separately and can be ported upstream when the recipes catalog is writable.