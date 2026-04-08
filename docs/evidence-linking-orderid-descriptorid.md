# Evidence linking for `orderId` and `descriptorId`

## Purpose

This note defines how agentplane execution artifacts should retain references back to upstream governed work and knowledge objects.

## Required references

When available, execution artifacts SHOULD preserve:
- `orderId`
- `descriptorId`
- upstream workspace evidence refs
- policy pack ref or hash when relevant

## Why this matters

These references make it possible to:
- trace governed work from request to execution to replay
- connect execution evidence back to the knowledge commons
- preserve a stable audit trail across repos and systems

## Constraint

This reference linkage does not make `agentplane` the source of truth for descriptor semantics. It only preserves durable identifiers needed for audit and replay.
