# Event Capability Admission Reconciliation — 2026-05-23

Issue: `SocioProphet/agentplane#168`

Source branch audited:

```text
work/event-capability-admission-refresh
```

## Finding

The stale branch payload is already present on current `main`:

```text
docs/integration/event-capability-admission.md
examples/orchestration/event-capability.records.json
scripts/validate_event_capability_admission.py
```

The mainline documentation is stricter than the stale branch because it includes validation-posture language clarifying that normal bootstrap validation admits mixed states while strict mode is reserved for future slices.

## Current replay action

This reconciliation PR adds the missing focused workflow gate:

```text
.github/workflows/event-capability-admission.yml
```

## Boundary

This replay adds validation coverage only.

It does not add event execution, provider calls, device/action mutation, network activity, or external writes.
