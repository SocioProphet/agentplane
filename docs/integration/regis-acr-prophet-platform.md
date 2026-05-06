# Integration guide: Regis / ACR → Prophet Platform → agentplane

Version: v0.1
Status: draft integration guide
Owner: agentplane

## Purpose

This guide defines how Regis Entity Graph / Authority Concordance Rex (ACR) service work becomes an evidence-producing agentplane execution.

Regis owns entity, evidence, concordance, decision-ledger, energy-ledger, promotion-policy, and relationship-formation semantics. Prophet Platform hosts the deployable `regis-acr-api` runtime. agentplane validates and runs bounded bundles that exercise the service and emits tamper-evident Validation, Placement, Run, and Replay artifacts.

## Existing stack fit

agentplane already follows the execution sequence:

```text
Bundle → Validate → Place → Run → Evidence → Replay
```

For Regis / ACR, the service slice is:

```text
Regis domain contracts → Prophet Platform service fixture → agentplane Bundle → RunArtifact / ReplayArtifact / Receipt
```

## Canonical ownership split

| Concern | Owner |
|---|---|
| Entity/evidence/concordance domain contracts | `SocioProphet/regis-entity-graph` |
| Runtime service and deployment topology | `SocioProphet/prophet-platform/apps/regis-acr-api` |
| Cross-estate registry and workspace truth | `SocioProphet/sociosphere` |
| Execution admission, placement, run, replay evidence | `SocioProphet/agentplane` |
| Lifecycle/formation semantics | `SocioProphet/ontogenesis` |
| Policy verdicts and promotion gates | `SocioProphet/policy-fabric` |
| Transport metadata | `SocioProphet/tritrpc` |

## Bundle target

Recommended bundle path:

```text
bundles/regis-acr-service-smoke/
```

Recommended artifact path:

```text
artifacts/regis-acr-service-smoke/
```

The bundle should validate that the Prophet Platform service can execute the minimum ACR service path:

1. health probe
2. source-record ingest
3. concordance proposal
4. promotion evaluation blocked by low margin
5. promotion evaluation eligible only for evidence-first insertion when gates pass
6. relationship-formation hook emission for Ontogenesis binding

## Required upstream artifact refs

When this bundle is generated from SocioSphere, preserve upstream references through the existing `SOCIOSPHERE_*` seam:

```bash
export SOCIOSPHERE_WORKSPACE_INVENTORY_REF="ref://sociosphere/workspace/<workspace>@sha256:<hash>"
export SOCIOSPHERE_LOCK_VERIFICATION_REF="ref://sociosphere/lock/<workspace>@sha256:<hash>"
export SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF="ref://sociosphere/compat/<workspace>@sha256:<hash>"
export SOCIOSPHERE_TASK_RUN_REFS="ref://sociosphere/taskrun/<run>"
```

agentplane records these references in RunArtifact and ReplayArtifact. SocioSphere remains responsible for validating workspace composition and lock state.

## Required ACR evidence behavior

The run must prove the service is safety-shaped:

- source record ingest returns evidence claims and a decision-ledger entry
- concordance proposal returns `pending_review`, not automatic canonical mutation
- low-margin promotion returns blocked or review-required
- relationship hook returns Ontogenesis binding requirements
- every consequential response returns receipt metadata or receipt-compatible fields

## Admission and policy posture

Initial bundle execution is allowed only when:

- `metadata.licensePolicy.allowAGPL` is `false`
- `spec.policy.maxRunSeconds` is bounded
- no inline secrets are present
- the service run is fixture-backed or local-only unless an explicit route/policy grant exists
- promotion policy is evidence-first and non-mutating by default

## Non-goals for the first tranche

- no production database mutation
- no irreversible canonical merge
- no cross-prime identity aggregation
- no external service egress unless a Network Door / BYOM plan explicitly allows it
- no Ontogenesis lifecycle activation without its own validated transition

## Run order

1. SocioSphere validates the multi-repo workspace and emits upstream refs.
2. Prophet Platform provides the `regis-acr-api` service and smoke command.
3. SocioSphere or a developer assembles `bundles/regis-acr-service-smoke/bundle.json`.
4. agentplane validates the bundle.
5. agentplane selects executor.
6. agentplane runs the service smoke.
7. agentplane emits ValidationArtifact, PlacementDecision, RunArtifact, ReplayArtifact, and receipt-compatible records.

## Acceptance criteria

The integration is considered aligned when:

- `SocioProphet/regis-entity-graph` has validating ACR schemas and examples.
- `SocioProphet/prophet-platform` has `regis-acr-api` service code, smoke tests, and Makefile targets.
- `SocioProphet/agentplane` has a bundle or bundle spec for `regis-acr-service-smoke`.
- RunArtifact and ReplayArtifact contain SocioSphere upstream artifact refs.
- The service smoke demonstrates evidence-first, no-auto-merge behavior.

## Next implementation tranche

1. Add `bundles/regis-acr-service-smoke/bundle.json`.
2. Add `bundles/regis-acr-service-smoke/smoke.sh` that invokes Prophet Platform's Regis ACR smoke target or local service endpoints.
3. Add any schema or README index updates needed for the bundle.
