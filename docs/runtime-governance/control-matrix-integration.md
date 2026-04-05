# Runtime governance integration plan

This document defines the first expected binding points for the imported control bundle.

## Initial enforcement surfaces

1. Policy gate
   - import the compiled policy bundle
   - deny / warn / require approval according to row-derived blocker logic
   - emit evidence for every evaluated control cell

2. Monitor lane
   - ingest generated monitor bundle definitions
   - attach monitor health and stale-review checks
   - reconcile incidents back to row IDs

3. Generated test lane
   - ingest generated test bundle definitions
   - run high-risk row checks on integration and release paths

## Evidence expectations

Runtime actions should emit:

- row id
- bundle version
- decision
- evidence references
- incident linkage when applicable
- exception linkage when applicable

## Control loop

The runtime lane should eventually close the loop:

monitor breach -> incident -> change proposal -> bundle regeneration -> review -> redeploy
