# SourceOS stage evidence

This note records the minimum evidence target for the `sourceos-asahi-stage` bundle.

## Current expectation

A successful stage run should emit a small stage-health artifact that records:

- whether required mounts were present,
- whether required secret-file paths were present,
- whether the stage bundle completed successfully,
- references back to the workstation contract and the typed substrate contracts.

## Example artifact

See `examples/receipts/sourceos-asahi-stage/stage-health.example.json`.

## Why this exists

The initial stage bundle landed before the full receipt surface was formalized. This note and example establish the first explicit artifact target for that bundle so later implementation can tighten the smoke script and artifact emission without changing the conceptual evidence contract.
