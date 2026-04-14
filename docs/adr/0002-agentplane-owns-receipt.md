# ADR-0002: agentplane owns the MAIPJ run receipt

Date: 2026-04-05  
Status: Accepted

## Context

A MAIPJ run receipt is the authoritative record of a governed AI execution. It aggregates
evidence from multiple subsystems: workspace state (sociosphere), context selection
(slash-topics), policy evaluation (human-digital-twin), transport metadata (TriTRPC), and
execution outcome (agentplane). Someone must own the receipt — i.e., assemble it, validate it
against the schema, and sign it.

Several candidates were considered:

- `sociosphere` — knows workspace state, but is not aware of execution outcome.
- `agentplane` — orchestrates the entire execution path from bundle validation through replay.
- `socioprophet-standards-storage` — owns normative schemas but has no runtime presence.
- A dedicated "receipt service" — would add an unnecessary new dependency.

## Decision

`agentplane` assembles, validates, and emits the MAIPJ run receipt. It collects the normalized
event stream produced by all participating subsystems, joins events by `trace_id`, validates the
assembled receipt against the schema, and refuses to emit if required fields are missing.

The reference implementation is in
[examples/receipts/agentplane_live_receipt_emitter_reference.py](../../examples/receipts/agentplane_live_receipt_emitter_reference.py).

See the field ownership table in
[docs/receipt-lifecycle.md](../receipt-lifecycle.md) for which subsystem contributes which
receipt fields.

## Consequences

- **Positive:** A single authoritative receipt emitter; no ambiguity about who seals the record.
- **Positive:** agentplane already has the execution timeline and can enforce the energy-sum
  invariant (`energy_j.total` = sum of all component fields).
- **Negative:** agentplane must wait for events from all participating subsystems before
  finalizing the receipt. This creates a temporal coupling that must be managed carefully in
  async/distributed execution paths.
- **Negative:** If a participating subsystem fails to emit its required events, agentplane must
  surface a clear error rather than emitting a partial receipt.
