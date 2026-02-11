# ExecutorAPI (v0.1)

Goal: a stable contract for tools that **apply changes** and **run commands** in a working tree.

## Required operations

- `plan(task, context) -> Plan`
- `apply(plan) -> ApplyResult`
- `run(command, cwd, env) -> RunResult`
- `diff() -> Diff`
- `snapshot() -> SnapshotRef` (optional; for evidence)

## Evidence requirements

Every Executor must emit:
- applied diff (unified diff or patch ID)
- stdout/stderr + exit code
- tool/version identifiers
- inputs (task ID, repo ref) and outputs (artifacts)

## Providers (examples)

- OpenCode
- Goose
- Aider
- Continue
