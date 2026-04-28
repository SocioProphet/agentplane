# Complies with Standards — Multi-Domain Geospatial Intelligence

Status: Draft agent-runtime conformance

This execution-control repository consumes the SocioProphet multi-domain geospatial standards package.

## Standards consumed

- `SocioProphet/prophet-platform-standards/docs/standards/070-multidomain-geospatial-standards-alignment.md`
- `SocioProphet/prophet-platform-standards/registry/multidomain-geospatial-standards-map.v1.json`
- `SocioProphet/socioprophet-standards-storage/docs/standards/096-multidomain-geospatial-storage-contracts.md`
- `SocioProphet/socioprophet-standards-knowledge/docs/standards/080-multidomain-geospatial-knowledge-context.md`
- `SocioProphet/socioprophet-agent-standards/docs/standards/020-multidomain-geospatial-agent-runtime.md`
- `SocioProphet/socioprophet-agent-standards/schemas/jsonschema/multidomain/geospatial_agent_runtime_profile.v1.schema.json`

## Implementation responsibility

`Agentplane` owns approval-gated execution for multi-domain geospatial runtime candidates.

Agentplane MUST ensure that runtime candidates define:

- runtime ID and version
- schema-bound inputs and outputs
- policy bundle references
- sensitive geospatial handling
- approval requirement
- evidence bundle outputs
- replay metadata
- failure/rollback semantics

## Required execution gates

- standards cross-reference gate
- approval-required gate for sensitive, defense/public-safety, or privileged writes
- evidence bundle gate
- replay metadata gate
- source license/redistribution gate
- redaction/masking gate

## Safety boundary

Agentplane may execute authorized ingest, transformation, analytics, report, and advisory tasking workflows. It must not execute ungoverned targeting, evasion, sensitive-site exploitation, or unauthorized tracking workflows.

## Promotion gate

A multi-domain geospatial execution candidate is draft until it validates against `socioprophet-agent-standards` and references storage and knowledge standards for inputs and outputs.
