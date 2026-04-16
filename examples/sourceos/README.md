# SourceOS local control node examples

This directory captures example payloads handed from the local control node / Node Commander lane into `agentplane`.

## Current example

- `local-control-node-promotion-input.example.json`

## What it expresses

The current example shows the downstream seam for:

- `ControlNodeProfile` reference
- `NodeCommanderRuntime` reference
- candidate build reference
- target image reference
- image promotion gate reference
- build validation evidence bundle reference
- scenario outcomes produced before promotion

## Expected agentplane outputs

The example also makes explicit the downstream artifact families that `agentplane` should emit or bind:

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact`
- `ReplayArtifact`

This file is intentionally narrow and additive. It does not redefine the canonical typed contracts owned by `sourceos-spec`.
