# ADR-0004: GAKW as the first live benchmark path

Date: 2026-04-05  
Status: Accepted

## Context

The first live integration path for the MAIPJ run receipt requires choosing a benchmark family
that forces all critical layers to participate simultaneously:

- workspace / manifest state
- governed context packs
- deterministic transport
- execution control plane
- policy and human approval
- evidence / replay
- mission-weighted utility accounting

Several benchmark families were considered:

- **Robotics control** — Requires exotic hardware; not available for the first path.
- **Batch training** — Does not exercise the context-pack or approval layers meaningfully.
- **GAKW (Governed Assistive Knowledge Work)** — Uses governed context packs, crosses local and
  remote boundaries, can require human approval, is replayable, and is not blocked on exotic
  hardware.

## Decision

GAKW (`gakw_hybrid_warm_answer`) is the first live benchmark case for the MAIPJ receipt
integration path.

This is a better first benchmark than a bare model invocation because it forces all critical
layers to participate and makes the resulting baseline meaningful for future A/B comparisons
(e.g., edge vs. cloud vs. hybrid placement with the same task and utility rubric).

The example trace is in
[examples/receipts/gakw_hybrid_warm_trace.example.json](../../examples/receipts/gakw_hybrid_warm_trace.example.json).

## Consequences

- **Positive:** The first benchmark exercises the full receipt assembly pipeline end-to-end.
- **Positive:** GAKW cases can be extended to A/B placement comparisons after the first baseline.
- **Negative:** GAKW requires `slash-topics` context packs and a `human-digital-twin` policy
  bundle to be available; the first live path cannot be run without those subsystems.
- **Negative:** Robotics and batch-training benchmark families will need separate first-path
  designs when the time comes.
