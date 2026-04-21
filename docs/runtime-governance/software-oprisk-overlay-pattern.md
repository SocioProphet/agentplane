# Software Operational Risk Overlay Pattern

This note documents the pragmatic pattern used by the first structured execution examples in the software operational risk lane.

## Why an overlay pattern exists

The current `agentplane` artifact family already contains the core execution evidence artifacts.

The immediate need is not necessarily a brand-new artifact schema family.
It is a disciplined way to associate existing execution evidence with the typed software operational risk objects that now exist upstream.

## Current pattern

The first structured examples use a **companion overlay** shape that records:

- the execution phase,
- the execution artifact reference,
- a summary,
- typed references to operational-risk objects,
- and execution notes describing why the linkage matters.

## Current example overlays

- `examples/receipts/software-oprisk-degraded-run-overlay.json`
- `examples/receipts/software-oprisk-rollback-overlay.json`

## Why this is useful

This pattern lets the platform demonstrate operational-risk linkage now, while leaving open a later decision about whether references should:

1. be embedded directly into existing runtime artifacts, or
2. live in a companion receipt overlay family.

## Immediate follow-on

1. Decide whether the overlay pattern graduates into a typed contract.  
2. Add one structured replay / investigation example.  
3. Add one structured promotion / reversal governance example tied to the same operational-risk family.
