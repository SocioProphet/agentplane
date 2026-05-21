# Bounded Action Loop v0

Status: v0.1 bounded contract surface.

This document defines the first Agentplane carrier for the Watson/Cyc/Semantic-Web/CHRONOS deployable loop.

## Purpose

Agentplane owns the runtime-control seam. This v0 tranche provides a bounded local carrier for an action proposal, policy decision reference, runtime trace, and outcome record without adding external side effects or autonomous execution behavior.

The intended integration path is:

```text
Sherlock source-quality answer trace
  -> Ontogenesis corpus event semantics
  -> Policy Fabric decision
  -> Agentplane bounded proposal and trace
  -> Model Governance Ledger record
```

## Added surfaces

```text
schemas/bounded-action-loop.v0.schema.json
tests/fixtures/bounded-action-loop/valid.record-event-instance.json
tests/fixtures/bounded-action-loop/invalid.missing-policy-decision.json
tests/fixtures/bounded-action-loop/invalid.external-side-effects.json
tools/check_bounded_action_loop.py
```

## Validation

Run:

```bash
make validate-bounded-action-loop
```

The target is included in:

```bash
make validate
```

The checker validates schema shape and rejects loops where:

- proposal, trace, and outcome references do not align;
- policy decision references are missing;
- evidence references are empty;
- a recorded trace is paired with non-low risk in v0;
- the bounded trace declares external side effects.

## Boundary

This tranche does not add executor behavior, external effects, model calls, host mutation, autonomous engagement, or self-modifying behavior. It provides the v0 carrier and fixture checks only.
