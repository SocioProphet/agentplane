# AOKC implementation checklist for agentplane v0.1

## Purpose

This checklist turns the order-to-bundle bridge note into an implementation-facing work surface.

## Required bridge work

- preserve `orderId` in execution metadata
- preserve `descriptorId` in execution metadata when available
- map `policyPackRef` into bundle policy fields
- map `policyPackHash` into bundle policy fields when present
- map `humanGateRequired` into bundle policy fields
- map `maxRunSeconds` into bundle policy fields

## Evidence work

Execution artifacts should retain:
- `orderId`
- `descriptorId`
- upstream evidence refs
- policy pack refs or hashes when relevant

## Non-goals

- agentplane should not own knowledge taxonomy
- agentplane should not become the source of truth for content spaces
- agentplane should not inline the full descriptor graph into bundles

## Ready-to-code gate

The bridge is ready for code work when:
1. the standards and transport PRs are merged
2. a stable order payload example exists
3. the target bundle fields are explicitly identified
4. emitted artifacts have a documented place for stable ids and evidence refs
