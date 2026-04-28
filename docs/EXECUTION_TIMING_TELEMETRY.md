# Execution Timing Telemetry

Agentplane records timing telemetry as first-class execution evidence.

## Role

Agentplane is the per-run source of truth for governed execution timing. It records task, agent, command, queue, run, completion, artifacts, evidence, and replay references.

Global DevSecOps Intelligence aggregates timing across repos and agents.

SocioSphere rolls timing into program/workstream dashboards.

Policy Fabric defines required timing fields and merge gates.

Alexandrian Academy converts failures and timing patterns into lessons, evals, and retraining material.

## Required fields

Each timing-aware execution record must include:

- `taskId`
- `agentId`
- `agentKind`
- `workstream`
- `repo`
- `issueRef` or `taskRef`
- `command`
- `queueStartedAt`
- `runStartedAt`
- `runCompletedAt`
- `wallClockMs`
- `status`
- `exitCode`
- `retryCount`
- `stdoutRef`
- `stderrRef`
- `artifactRefs`
- `evidenceRef`
- `replayRef`

## Validation rule

`wallClockMs` must equal `runCompletedAt - runStartedAt` in milliseconds.

`queueStartedAt <= runStartedAt <= runCompletedAt` must hold.

Raw prompts, stdout, stderr, and artifacts should be referenced by evidence/artifact refs unless explicitly safe to inline.
