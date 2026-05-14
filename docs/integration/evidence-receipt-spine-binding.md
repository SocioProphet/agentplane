# Evidence Receipt Spine Binding v0

## Status

Proposed AgentPlane binding.

## Purpose

This note maps AgentPlane runtime artifacts onto the merged SocioProphet evidence receipt spine without replacing the existing AgentPlane artifact schemas.

AgentPlane already owns evidence-forward execution artifacts such as `ValidationArtifact`, `RunArtifact`, `ReplayArtifact`, and `PromotionArtifact`. The standards layer now owns the cross-repo receipt spine:

- `ValidationReceipt`
- `PromotionReceipt`
- `ExecutionReceipt`
- `ReplayReceipt`

The binding in this repo records how an AgentPlane artifact is linked to the canonical receipt family.

## Non-goals

This binding does not:

- replace existing AgentPlane artifact schemas;
- redefine `socioprophet-standards-storage` receipt schemas;
- redefine Knowledge Context lifecycle states;
- add runtime emission logic;
- authorize merge, deployment, or side effects.

## Canonical mapping

| AgentPlane artifact | Receipt kind | Intended use |
|---|---|---|
| `ValidationArtifact` | `ValidationReceipt` | Bundle validation and control-gate validation evidence. |
| `PromotionArtifact` | `PromotionReceipt` | Promotion into a more durable or production-facing state. |
| `RunArtifact` | `ExecutionReceipt` | Governed runtime execution evidence. |
| `ReplayArtifact` | `ReplayReceipt` | Replay boundary and reproducibility evidence. |

## Binding object

The `AgentPlaneEvidenceReceiptBinding` object records:

- the AgentPlane artifact reference;
- the AgentPlane artifact kind;
- the canonical receipt identifier;
- the canonical receipt kind;
- the subject reference shared by both surfaces;
- the standards documents being consumed;
- the concrete field mappings used by downstream consumers.

## Authority split

| Surface | Owner |
|---|---|
| AgentPlane artifact schemas | `SocioProphet/agentplane` |
| Evidence receipt spine | `SocioProphet/socioprophet-standards-storage` |
| Knowledge state lifecycle | `SocioProphet/socioprophet-standards-knowledge` |
| Transport framing | `SocioProphet/TriTRPC` |
| Policy verdicts | `SocioProphet/policy-fabric` |

AgentPlane may bind to receipt identifiers, but it does not own the canonical receipt schema vocabulary.

## First implementation path

The first implementation path is intentionally narrow:

1. Add a binding schema and example fixture.
2. Validate the binding fixture with a stdlib-only validator.
3. Wire the validator into `make validate`.
4. Later, emit these binding objects from runtime paths once runtime receipt generation is implemented.

## Follow-on backlog

- Add runtime emitters for receipt bindings.
- Add `DiffHygieneGateReport` to `ValidationReceipt` mapping once Policy Fabric verdict export is stable.
- Add FogStack runtime record to `ExecutionReceipt` / `ReplayReceipt` mapping in `prophet-platform`.
- Add optional receipt reference fields to artifact schemas only after the binding shape is accepted.
