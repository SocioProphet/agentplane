# Semantic control binding plan

This document defines how `SCTControlProfile` binds into AgentPlane execution and evidence.

## Bundle insertion point

Until `schemas/bundle.schema.v0.1.json` is amended directly, the feature is carried as an extension under:

- `spec.policy.semanticControl`

Expected fields are defined in:

- `schemas/extensions/semantic-control.fragment.v0.1.json`

## Validation flow

`validate_bundle.py` should eventually perform the following steps in order:

1. load bundle JSON
2. validate ordinary bundle contract
3. if `spec.policy.semanticControl` is present:
   - resolve `profileRef`
   - load the profile bytes
   - validate against `schemas/sct-control-profile.schema.v0.1.json`
   - compute canonical `profileHash`
   - verify the declared `profileHash`
   - verify signature from `profileSignatureRef`
   - verify `authorizedAudience` against the current executor / tenant / agent identity
   - check `issuedAt` / `expiresAt`
   - derive `sctProjection`
4. evaluate control matrix gate with the derived projection included in context
5. emit `validation-artifact.json`
6. emit `control-gate-artifact.json`

## Derived projection

The profile is converted into execution-safe fields only.

Minimum projection:

- `lane`
- `plannerBranchBudget`
- `toolBudget`
- `memoryScope`
- `disclosureScope`
- `handoffPolicy`
- `interruptPolicy`
- `humanGateRequired`
- `maxRunSeconds`
- `breakGlassAllowed`
- `breakGlassReasonRequired`

## Artifact bindings

The following evidence artifacts should include semantic-control bindings:

### ValidationArtifact
- `sctProfileRef`
- `sctProfileHash`
- `sctProfileKeyId`
- `sctProfileAudience`
- `sctProjection`
- `sctValidationResult`

### ControlGateArtifact
- `sctProfileHash`
- `sctProjection`
- `sctFailMode`
- `sctAudienceResult`
- `sctExpiryResult`

### PlacementDecision
- `sctProfileHash`
- `sctProjection`

### RunArtifact
- `sctProfileHash`
- `sctProjection`
- `sctRuntimeReceipt`

### ReplayArtifact
- `sctProfileHash`
- `sctProjection`
- `sctReplayBound`

## Unauthorized handling

If the semantic control profile is missing, malformed, unauthorized, or expired:

- default is fail closed
- optional alternative is degrade or human-escalate depending on `failMode`
- unauthorized requests should emit telemetry but not expose profile contents

## Minimal rollout sequence

1. land schema and extension fragment
2. land example bundle and example profile
3. patch validation to parse and verify profile
4. patch control gate to bind profile context
5. patch artifact schemas and emitters
6. add regression tests for authorized / unauthorized / expired / malformed cases
