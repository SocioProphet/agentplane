# Policy Fabric verdict envelope v0

## Status

Plan/spec document.

This document binds the first machine-readable execution-side envelope for Policy Fabric verdict consumption into Agentplane.

## Purpose

Agentplane needs a narrow typed envelope that can be consumed at execution eligibility time without importing the entire upstream authored-policy model.

The envelope should carry:
- governing policy bundle identity
- target domain
- rights-critical flag
- promote / block result
- fit classification
- failed predicates and reason strings
- threshold context
- references to upstream verdict artifacts

## Intended schema

The first schema for this seam is:

- `schemas/policy-fabric-verdict-envelope.schema.v0.1.json`

## Why this is not the same as the upstream verdict report

The upstream Policy Fabric verdict report is the broader evidence-bearing control artifact.

The Agentplane envelope is the downstream execution-facing consumption surface. It should stay narrow enough to be attached to execution gating and downstream evidence artifacts.

## Follow-on

A later implementation tranche should:
1. validate this envelope before governed execution proceeds
2. fail closed when the envelope is missing or indicates `promote = false`
3. preserve the envelope references in downstream evidence artifacts
