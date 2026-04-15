# Semantic proof and export bindings

Agentplane does not decide semantic identity or export readiness by itself. It consumes governance references produced elsewhere and carries them through validation, run, replay, and session artifacts.

## Governance context

`spec.governanceContext` on a bundle is the runtime binding point for:

- workload principal (`spiffe_id`, `aum_digest`, optional `session_id`)
- grant reference
- policy decision reference and `policyHash`
- semantic identity evidence refs (`eventIrRef`, `proofArtifactRef`)
- export/readiness evidence refs (`hdtDecisionSummaryRef`)
- attestation and transport receipt refs
- control-matrix row / exception / incident refs

## Runtime propagation

When present, validation, run, replay, and session artifacts propagate the governance context so downstream replay and review can explain *why* an execution was allowed and *which evidence* supported it.

## Profiles

For prod-lane bundles, `governanceContext` and `policyHash` are required by the validator.
