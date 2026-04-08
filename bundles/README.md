# bundles

Bundles are the unit of deployment in agentplane.

A bundle directory contains:

| File | Purpose |
|---|---|
| `bundle.json` | Manifest: metadata, policy, executor hint, artifact dir, smoke script ref, VM spec |
| `vm.nix` | NixOS module defining the guest environment |
| `smoke.sh` | Smoke test script (runs on host or inside the guest VM) |

The bundle schema is defined in [`schemas/bundle.schema.v0.1.json`](../schemas/bundle.schema.v0.1.json).
Validate a bundle with:

```bash
python3 scripts/validate_bundle.py bundles/<name>/bundle.json
```

Runners execute bundles (`qemu-local` today; `microvm`/`fleet` later). See
[`runners/runner.md`](../runners/runner.md) for the backend-agnostic runner contract.

---

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

- `metadata.source.git.rev` — Should be set to the actual commit SHA before merging to main.
  When running `scripts/pr.sh`, consider setting this via a pre-commit step.
- `spec.policy.policyPackHash` — Should be set to the SHA-256 hash of the referenced policy
  pack. Leave as `"UNSET"` during development when no real policy pack is pinned.

### Run the example

```bash
# Full demo: hygiene → doctor → validate → run → emit artifacts
scripts/demo.sh

# Or run the bundle directly
runners/qemu-local.sh run bundles/example-agent --profile staging --watch
```

Artifacts are written to `artifacts/example-agent/`.
