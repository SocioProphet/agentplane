# Event Capability Admission

Status: bootstrap integration guide

AgentPlane must treat event-driven orchestration as evidence-producing execution, not as an implicit callback path. An event may propose work, but the work is not executable until admission proves idempotency, policy outcome, evidence references, and high-risk approval posture.

## Contract source

The canonical event capability fixture currently lives in `SocioProphet/prophet-platform`:

- `specs/orchestration/event_capability_fixture.py`

It exports flattened records with:

```bash
python specs/orchestration/event_capability_fixture.py --events
```

AgentPlane consumes those records through:

```bash
python scripts/validate_event_capability_admission.py --input examples/orchestration/event-capability.records.json
```

## Admission states

- `admitted` — policy outcome is executable in the bootstrap lane, currently `allowed` or `redacted`.
- `waiting_for_approval` — policy outcome requires approval; AgentPlane must not execute until approval evidence exists.
- `blocked` — policy outcome is denied, degraded, or local-only constrained.
- `invalid` — the record lacks mandatory evidence, idempotency, policy, or dead-letter controls.

## Non-negotiable invariants

1. Every event reaction must have an idempotency key.
2. Every reaction must carry evidence receipt references.
3. Every reaction must be dead-letterable on failure.
4. High-risk capabilities cannot be directly allowed in the bootstrap lane.
5. High-risk approval must use explicit, two-party, or admin approval mode.
6. Policy outcome must match the capability-required outcome.
7. Degraded or denied records remain evidence, not executable work.

## Validation posture

The bootstrap validator is intentionally non-mutating. A passing validation means records are admissible for the next control-plane step, not that any device, provider, shell, or external system should be touched.

Strict mode is reserved for future slices where every record is expected to be executable. The bootstrap fixture intentionally includes blocked and approval-required records, so the normal validation path must allow those states while still rejecting invalid records.

## Execution posture

This validator does not execute a routine, mutate a device, call a provider, or write to external systems. It emits an `agentplane.event_capability_admission.v0.1` artifact that can be stored beside other AgentPlane evidence artifacts and used as a stop gate before guarded execution.

The world-class target is an event-native execution membrane:

`event -> capability -> policy -> admission -> approval if needed -> guarded execution -> receipt -> replay/dead-letter`
