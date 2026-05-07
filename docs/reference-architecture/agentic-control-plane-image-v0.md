# Agentic Control Plane Image Companion v0

Status: Informative reference note.

This file accompanies a visual control-plane image asset for orientation only.

## Purpose

The image is useful for fast orientation across the following layers:

- client, operator, and API surfaces;
- core agentic control plane;
- security, governance, and policy plane;
- planning and reasoning services;
- execution and runner plane;
- integration adapters;
- capability and worker plane.

## Rule

The image is not the source of normative truth.

Normative truth remains in:
- versioned schemas;
- executable validators;
- policy-fabric contracts;
- planning/transport contracts;
- runtime evidence artifacts.

## Reading guidance

When using the image, preserve these boundaries:

1. implementation, review, and merge authority remain separate;
2. policy gates own admissibility and merge decisions;
3. runners emit evidence rather than inventing policy;
4. adapters pass references and evidence, not shadow authoritative state;
5. visual layers do not override repository ownership.

## Expected companion

This image should be read together with:
- `docs/reference-architecture/agentic-control-plane-v0.md` when that note is merged;
- current runtime-governance notes;
- policy-fabric gate contracts;
- semantic-serdes verification artifact contracts;
- TriTRPC planning-service contracts.
