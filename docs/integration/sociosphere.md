# Integration guide: sociosphere → agentplane

This guide explains how to run an agentplane bundle that originates from a `sociosphere`
workspace, including how to pass upstream workspace artifacts so they appear in the
`RunArtifact` and `ReplayArtifact`.

For the conceptual overview of the seam, see [docs/sociosphere-bridge.md](../sociosphere-bridge.md).  
For the relevant ADRs, see [ADR-0003](../adr/0003-sociosphere-owns-workspace-truth.md) and [ADR-0006](../adr/0006-narrow-sociosphere-seam.md).

---

## Prerequisites

- `sociosphere` has validated the workspace and emitted its upstream artifacts.
- `sociosphere` has generated a valid `bundle.json` (conforming to
  [schemas/bundle.schema.v0.1.json](../../schemas/bundle.schema.v0.1.json)).
- The bundle directory is accessible on the control-plane host.

---

## Run order

The intended sequence (from [docs/sociosphere-bridge.md](../sociosphere-bridge.md)):

1. `sociosphere` validates workspace composition and emits upstream artifacts.
2. `sociosphere` generates a valid Bundle.
3. `agentplane` validates the bundle.
4. `agentplane` selects an executor.
5. The runner backend performs the run.
6. `agentplane` emits `RunArtifact` and `ReplayArtifact` into the bundle artifact directory.

---

## Passing upstream artifact references

`sociosphere` communicates its artifact references to `agentplane` via four environment
variables. Set these before invoking any agentplane script:

```bash
export SOCIOSPHERE_WORKSPACE_INVENTORY_REF="ref://sociosphere/workspace/my-workspace@sha256:abc"
export SOCIOSPHERE_LOCK_VERIFICATION_REF="ref://sociosphere/lock/my-workspace@sha256:def"
export SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF="ref://sociosphere/compat/my-workspace@sha256:ghi"
export SOCIOSPHERE_TASK_RUN_REFS="ref://sociosphere/taskrun/run1,ref://sociosphere/taskrun/run2"
```

These values are passed through unmodified into:

- `RunArtifact.upstreamArtifacts` (written by `scripts/emit_run_artifact.py`)
- `ReplayArtifact.inputs.upstreamArtifacts` (written by `scripts/emit_replay_artifact.py`)

They also flow into the receipt's `_workspace` block during assembly.

**agentplane does not validate these references.** It records them as-is. The correctness
of the referenced artifacts is `sociosphere`'s responsibility (see [ADR-0003](../adr/0003-sociosphere-owns-workspace-truth.md)).

---

## Step-by-step example

### 1. Set workspace artifact refs

```bash
export SOCIOSPHERE_WORKSPACE_INVENTORY_REF="workspace://gakw/hybrid-warm-answer"
export SOCIOSPHERE_LOCK_VERIFICATION_REF="sha256:lock-example"
export SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF="sha256:compat-example"
export SOCIOSPHERE_TASK_RUN_REFS=""
```

### 2. Validate the bundle

```bash
python3 scripts/validate_bundle.py path/to/bundle.json
```

This writes a `ValidationArtifact` to the bundle's `spec.artifacts.outDir`.

### 3. Select an executor

```bash
python3 scripts/select-executor.py path/to/bundle.json
```

This prints a `PlacementDecision` JSON to stdout. The runner calls this automatically.

### 4. Run the bundle

```bash
runners/qemu-local.sh run path/to/bundle-dir --profile staging
```

The runner:
- Validates the bundle
- Selects an executor
- Executes the bundle (lima-process or QEMU path)
- Emits `RunArtifact`, `ReplayArtifact`, `PlacementDecision`, `PlacementReceipt`
  into `spec.artifacts.outDir`

### 5. Emit artifacts explicitly (optional, for custom runners)

If you are implementing a custom runner backend rather than using `runners/qemu-local.sh`,
emit the run and replay artifacts manually:

```bash
# After the run completes with exit code $EXIT_CODE:
python3 scripts/emit_run_artifact.py \
    path/to/bundle.json \
    <executor-name> \
    $EXIT_CODE \
    --stdout path/to/stdout.log \
    --stderr path/to/stderr.log

python3 scripts/emit_replay_artifact.py \
    path/to/bundle.json \
    <executor-name> \
    --bundle-rev $(git rev-parse HEAD) \
    --bundle-path path/to/bundle-dir
```

### 6. Verify artifacts

```bash
ls -la $(python3 -c "import json; b=json.load(open('path/to/bundle.json')); print(b['spec']['artifacts']['outDir'])")
```

Expected files:

| File | Kind |
|---|---|
| `validation-artifact.json` | `ValidationArtifact` |
| `placement-decision.json` | `PlacementDecision` |
| `placement-receipt.json` | `PlacementReceipt` |
| `run-artifact.json` | `RunArtifact` |
| `replay-artifact.json` | `ReplayArtifact` |

---

## What `agentplane` does NOT do

- It does not re-scan the workspace to verify composition or lock state. That is `sociosphere`'s
  responsibility.
- It does not validate the upstream artifact references (it treats them as opaque strings).
- It is not the source of truth for context pack selection or policy evaluation.

---

## Troubleshooting

### Missing upstream artifact refs in RunArtifact

**Symptom:** `upstreamArtifacts.*` fields are `null` in `run-artifact.json`.  
**Cause:** The `SOCIOSPHERE_*` env vars were not set before invoking the runner or scripts.  
**Fix:** Set all four env vars before running (see step 1 above).

### Bundle validation fails with "allowAGPL must be false"

**Cause:** The bundle generated by `sociosphere` does not include `metadata.licensePolicy.allowAGPL: false`.  
**Fix:** Ensure `sociosphere`'s bundle generator always sets `metadata.licensePolicy.allowAGPL: false`.

### "no executor satisfies backend=qemu"

**Cause:** The bundle requests `qemu` or `microvm` backend but no executor with `kvm: true`
is available.  
**Fix:** If running on macOS/Lima, change `spec.vm.backendIntent` to `lima-process` in the
generated bundle, or ensure the executor has `caps.kvm: true`. The runner will fall back to
`lima-process` automatically when `kvm: false`.
