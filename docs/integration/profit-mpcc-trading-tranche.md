# Profit MPCC trading tranche intake

## Purpose

This note records the current relationship between `mdheller/profit-mpcc` and `SocioProphet/agentplane` for the trading/execution lane.

## Current stance

`profit-mpcc` is the upstream semantic/archive drafting root.

`agentplane` remains the execution control plane.

The relevant near-term export surfaces from `profit-mpcc` are:
- effect / approval semantics,
- trading event-family lifecycle,
- market-data / order-intent / execution-report / position-change / reconciliation contracts,
- execution-facing examples under the trading tranche.

## Governance rule

Treat the `profit-mpcc` trading tranche as upstream source material and import only stabilized contracts and examples.

Do not absorb the archive-native or metaphysical drafting surfaces wholesale.
