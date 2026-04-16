# SourceOS OS Build Boundary Integration

## Status

Draft.

## Purpose

This document describes the first `agentplane` integration posture for the SourceOS OS build / cybernetic boundary.

The upstream SourceOS contract seam is expected to define:

- `OSImage`
- `NodeBinding`
- `CyberneticAssignment`

`agentplane` is not the schema authority for those objects. It is a runtime consumer and evidence producer.

## Initial runtime role

The first `agentplane` slice SHOULD do three things:

1. validate imported runtime boundary inputs before execution
2. keep immutable image identity separate from runtime service/policy semantics
3. emit evidence showing which inputs were accepted for the run

## Recommended input posture

- `OSImage` MAY be referenced by URN and optional artifact metadata for provenance/evidence.
- `NodeBinding` SHOULD be resolved before execution to determine topology/fleet/update-ring context.
- `CyberneticAssignment` SHOULD define the runtime service identity, policy refs, and control profile context for the run.

## Non-goals for the first slice

- no attempt to make `agentplane` the canonical image-build system
- no attempt to redefine install-time enrollment semantics
- no attempt to replace upstream policy-fabric boundary gates

## First implementation artifact

The initial runnable helper is `scripts/validate_runtime_boundary.py`.

That script provides a narrow input check for imported boundary objects so that runtime work can fail closed before execution when the seam is obviously violated.
