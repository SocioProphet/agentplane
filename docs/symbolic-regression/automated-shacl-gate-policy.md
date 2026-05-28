# PROMETHEUS Automated SHACL Gate Policy

Status: v0.1 AgentPlane policy gate.

This document defines the machine-readable automated gate policy for PROMETHEUS symbolic-regression candidates.

The automated gate is an eligibility decision only. It is not final semantic admission, ontology promotion, policy admission, or runtime authority.

## Policy fields

The policy encodes:

- minimum dataset size
- NMSE ceiling
- complexity ceiling
- required units status
- replay hash verification requirement
- maximum CHRONOS governance flags
- eligible review surface
- decision boundary
- final admission permission

The initial policy requires:

- `minimumDatasetSize` at least 4
- `nmse` no greater than 0.001
- `complexity` no greater than 10
- `unitsStatus` equal to `consistent`
- `replayHashVerified` equal to true
- no CHRONOS governance flags
- `requestedReviewSurface` equal to `automated_shacl_gate`
- `finalAdmissionRequested` equal to false

## Boundary

The automated gate determines only whether a candidate may use the automated SHACL review surface.

It does not admit the candidate as a law.

It does not admit an SRAssertion.

It does not mutate Ontogenesis or WebProtege.

It does not create runtime authority.

Human review remains required when a candidate has low dataset support, excessive error, excessive complexity, unknown or inconsistent units, unverified replay, any CHRONOS governance flag, or a request for final admission.

## Validation

`tools/validate_prometheus_automated_gate_policy.py` evaluates a policy fixture and an evaluation fixture.

Positive fixture:

- `tests/fixtures/symbolic-regression/automated-gate-evaluation.valid.json`

Negative fixtures reject:

- low dataset size
- high NMSE
- high complexity
- units status not consistent
- replay hash not verified
- CHRONOS governance flag present
- final admission requested
- missing threshold field

## Issue linkage

This tranche implements the machine-readable policy required by AgentPlane issue #245.
