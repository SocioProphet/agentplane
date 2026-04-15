# Semantic control feature (SCTControlProfile)

## Purpose

`semanticControl` promotes Countertext/SCT semantics from an external experiment to a first-class AgentPlane control feature.

The feature is intended to:

- carry selective orchestration semantics as signed metadata
- project those semantics into execution-safe runtime knobs
- fail closed when the profile is missing, invalid, expired, malformed, or unauthorized
- bind the resulting profile hash into execution evidence

This feature is **not** a hidden control channel embedded in public content. Public artifacts may remain ordinary. The specialized control semantics travel in a signed sidecar object only delivered to entitled agents through a zero-trust delivery layer.

## Control object

The canonical sidecar object is `SCTControlProfile`.

See:

- `schemas/sct-control-profile.schema.v0.1.json`
- `schemas/extensions/semantic-control.fragment.v0.1.json`
- `examples/semantic-control/semantic-control-profile.example.json`

## Current insertion point

AgentPlane already has the correct enforcement seam:

- `scripts/validate_bundle.py`
- `scripts/evaluate_control_matrix_gate.py`
- `spec.policy` inside `schemas/bundle.schema.v0.1.json`

The feature should be carried under:

- `spec.policy.semanticControl`

until the bundle schema is amended directly.

## Runtime projection

The profile is not consumed as free-form prose. Validation must derive an execution-safe projection such as:

- lane
n- plannerBranchBudget
- toolBudget
- memoryScope
- disclosureScope
- handoffPolicy
- interruptPolicy
- humanGateRequired
- maxRunSeconds

## Evidence binding

Validation, control gate, run, and replay artifacts should all bind:

- `sctProfileRef`
- `sctProfileHash`
- `sctProfileKeyId`
- `sctProfileAudience`
- `sctProjection`

This ensures replay and audit can prove which semantic control profile governed the run.

## Hardening requirements

1. signature verification
2. canonical hashing
3. audience / entitlement check
4. expiration check
5. selective delivery only through authorized layer
6. fail-closed validation and control gate behavior
7. replay binding of the resolved profile hash
8. downgrade or redaction behavior for unauthorized agents
9. unauthorized-inference telemetry
10. key rotation support

## Recommended rollout

1. land schema and extension fragment
2. land validation-side parser and verifier
3. bind profile hash into `ValidationArtifact` and `ControlGateArtifact`
4. extend placement/run/replay artifacts
5. add authorized vs unauthorized regression tests
