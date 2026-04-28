# Profit MPCC trading lifecycle intake (v0)

## Purpose

This note stages the governed trading lifecycle emerging from `mdheller/profit-mpcc` for review inside the execution lane.

## Lifecycle chain

1. market-data event
2. signal event
3. order-intent event
4. approval event
5. execution-report event
6. position-change event
7. reconciliation event

## Why this matters to Agentplane

The execution lane needs a clear separation between:
- proposals,
- approvals,
- actual execution,
- state deltas,
- and reconciliation/compensation.

## Intake stance

This is an intake copy for review. It is not the canonical upstream source of truth.
