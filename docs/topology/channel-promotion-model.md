# Channel and promotion model

`agentplane` owns the execution and promotion control-plane model.

## Shared schema references

This repository should use the shared contract canon in `SocioProphet/socioprophet-agent-standards` for reusable cross-repo terms.

Initial shared references:

- `schemas/channel.schema.json`
- `schemas/capability.schema.json`

## Channels

Initial control-plane channels:

- `dev`
- `candidate`
- `stable`

These channels represent promoted environment pointers for accepted artifact sets.

## Promotion intent

A promotion event should carry at least:

- channel target
- artifact set reference
- source revision
- evaluation bundle reference
- rollback reference
- capability versions or capability map

## Practical rule

`agentplane` defines the lifecycle and evidence requirements for promotion, while the durable shared meaning of the channel and capability terms is carried by the standards repository.
