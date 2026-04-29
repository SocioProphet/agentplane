# bundles

Bundles are the unit of deployment in agentplane.

A bundle directory contains:

| File | Purpose |
|---|---|
| `bundle.json` | Manifest: metadata, policy, executor hint, artifact dir, smoke script ref, VM spec |
| `vm.nix` | NixOS module defining the guest environment |
| `smoke.sh` | Smoke test script, run on host or inside the guest VM |

The bundle schema is defined in [`schemas/bundle.schema.v0.1.json`](../schemas/bundle.schema.v0.1.json).
Validate a bundle with:

```bash
python3 scripts/validate_bundle.py bundles/<name>/bundle.json
```

Runners execute bundles. See [`runners/runner.md`](../runners/runner.md) for the backend-neutral runner contract.

## example-agent

The reference bundle. Use it as a template for new bundles.

| Value | Setting |
|---|---|
| `metadata.name` | `example-agent` |
| `metadata.version` | `0.1.0` |
| `spec.vm.backendIntent` | `lima-process` |
| `spec.policy.lane` | `staging` |
| `spec.policy.maxRunSeconds` | `20` |
| `spec.policy.humanGateRequired` | `false` |
| `spec.artifacts.outDir` | `./artifacts/example-agent` |

### UNSET values

Two fields in the example `bundle.json` are intentionally set to `"UNSET"`:

- `metadata.source.git.rev` should be set to the actual commit SHA before merging to main.
- `spec.policy.policyPackHash` should be set to the SHA-256 hash of the referenced policy pack. Leave as `"UNSET"` during development when no real policy pack is pinned.

### Run the example

```bash
scripts/demo.sh
runners/qemu-local.sh run bundles/example-agent --profile staging --watch
```

Artifacts are written to `artifacts/example-agent/`.

## professional-intelligence-client-opportunity-review

The first Professional Intelligence OS Gate 3 workflow bundle. It provides a recordable execution seam for the `client-opportunity-review` playbook and emits workflow-step, run, and replay artifacts.

| Value | Setting |
|---|---|
| `metadata.name` | `professional-intelligence-client-opportunity-review` |
| `metadata.version` | `0.1.0` |
| `spec.vm.backendIntent` | `lima-process` |
| `spec.policy.lane` | `staging` |
| `spec.policy.maxRunSeconds` | `30` |
| `spec.policy.humanGateRequired` | `true` |
| `spec.artifacts.outDir` | `./artifacts/professional-intelligence-client-opportunity-review` |
| `spec.vm.network.mode` | `none` |

### Validate the bundle

```bash
python3 scripts/validate_bundle.py bundles/professional-intelligence-client-opportunity-review/bundle.json
```

### Host smoke

```bash
AGENTPLANE_ARTIFACT_DIR=./artifacts/professional-intelligence-client-opportunity-review bash bundles/professional-intelligence-client-opportunity-review/smoke.sh
```

### Runner smoke

```bash
runners/qemu-local.sh run bundles/professional-intelligence-client-opportunity-review --profile staging --watch
```

Expected artifacts:

- `professional-intelligence-workflow-step.json`
- `run-artifact.json`
- `replay-artifact.json`

This bundle is intentionally narrow. It proves that a Professional Intelligence playbook step can be represented as an Agentplane bundle and can emit replayable evidence for downstream DelEx, Policy Fabric, ContractForge, Prophet Workspace, and Prophet Platform controls.
