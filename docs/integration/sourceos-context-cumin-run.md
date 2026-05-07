# SourceOS Context Cumin Run Contract

Status: dry-run contract

## Purpose

This document defines the AgentPlane contract for running `sourceos-context` through a Cumin remote-runner boundary instead of the operator Mac.

The current state is intentionally dry-run. It validates the command envelope, policy binding, expected artifacts, and side-effect constraints before live remote execution is implemented.

## Runner posture

AgentPlane must treat Cumin as the execution boundary for this lane.

```json
{
  "runnerType": "cumin",
  "executionMode": "dry_run",
  "forbidLocalMac": true
}
```

Mac-local execution is explicitly out of scope for this lane.

## Tool provider

The run references the previously registered constrained tool provider:

```text
agentplane://tool-provider/smart-tree-context-provider
```

The tool runtime is:

```text
sourceos-context
```

## Policy binding

The run must bind to Policy Fabric:

```text
policy-fabric://sourceos.repo_context.read_only
```

That policy preserves the established boundaries:

- bounded `~/dev/**` roots only;
- symlink traversal denied;
- unbounded home scans denied;
- system scans denied;
- repo writes denied;
- hooks denied;
- dashboard and PTY denied;
- external callbacks denied;
- Smart Tree native memory persistence denied;
- Lampstand publish requires an explicit flag.

## Allowed dry-run operation

The first fixture uses:

```bash
sourceos-context lampstand-publish ~/dev/smart-tree --format json
```

It intentionally omits `--publish`. This validates the Lampstand record envelope without local record ingestion.

## Expected artifacts

A successful dry-run should produce references for:

- adapter response;
- policy decision trace;
- tool provenance;
- Lampstand publish report;
- optional Memory Mesh promotion packet reference.

## Non-goals

- No live Cumin executor implementation.
- No Mac-local execution.
- No direct Lampstand mutation in the example.
- No Memory Mesh durable writeback.
- No Symbol / SmartPastCode extraction.
- No watch mode.
- No dashboard, PTY, hooks, smart-edit writes, or external callbacks.

## Acceptance criteria

- The JSON schema validates.
- The example validates.
- The validator fails if the runner changes from `cumin`.
- The validator fails if `forbidLocalMac` is not true.
- The validator fails if mutating side effects become true.
- The validator fails if the dry-run example includes `--publish`.
