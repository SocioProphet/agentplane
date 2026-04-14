# Receipt runtime promotion

This note describes the next step beyond the current receipt reference and smoke-test material.

## Goal

Promote receipt assembly from example-only status into a runtime-adjacent owned surface.

## Current state

The repository already contains:

- a live receipt integration plan
- example traces
- a strict reference assembler
- a smoke-test path

## Promotion direction

The next runtime-adjacent layer should provide:

- a stable receipt-building module or package
- one small command-line entrypoint for local assembly from normalized traces
- one narrow artifact-writing path that can be called by execution-plane tooling

## Boundary

`agentplane` owns execution-plane receipt assembly.
It should not absorb workspace-truth ownership from `sociosphere` or protocol canon from `TriTRPC`.

## Why this note exists

This keeps the runtime promotion direction explicit and prevents receipt logic from remaining permanently stranded in examples only.
