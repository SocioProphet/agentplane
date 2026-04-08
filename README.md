# agentplane

**agentplane** is the execution control plane for the SocioProphet AI+HW+State stack.  
It takes a validated _Bundle_, selects an executor, runs the bundle, and emits tamper-evident evidence artifacts (Validation, Placement, Run, Replay) that support deterministic replay and governed benchmarking.

License: [MIT](LICENSE)

---

## What agentplane does

```
Bundle → Validate → Place → Run → Evidence → Replay
```

1. **Validate** — `scripts/validate_bundle.py` checks the bundle against the JSON Schema and emits a `ValidationArtifact`.
2. **Place** — `scripts/select-executor.py` consults `fleet/inventory.json` and picks a reachable executor; emits a `PlacementDecision`.
3. **Run** — `runners/qemu-local.sh` executes the bundle on the chosen executor (today: Lima process or QEMU VM); emits a `RunArtifact`.
4. **Evidence** — `scripts/emit_run_artifact.py` and `scripts/emit_replay_artifact.py` seal the evidence record.
5. **Replay** — The `ReplayArtifact` records all inputs needed for a deterministic re-run.

Evidence artifacts are written to `spec.artifacts.outDir` inside the bundle.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| [Nix](https://nixos.org/download) (≥ 2.18) | VM builds (`nix build`) |
| Python 3 (≥ 3.9) | Validation and artifact scripts |
| [Lima](https://lima-vm.io) + `lima-nixbuilder` VM | Default local executor |
| `rsync` | Syncing repo and artifacts to/from Lima |
| `ssh` (BatchMode capable) | Executor reachability probes |
| `gh` CLI | Creating pull requests via `scripts/pr.sh` |

> **macOS + Linux targets:** Building NixOS VMs requires a remote Linux builder  
> (`nix.builders = ssh-ng://lima-nixbuilder …`). Run `scripts/doctor.sh` to verify.

---

## Quick start

```bash
# 1. Preflight: verify Nix builders and Python
scripts/doctor.sh

# 2. Verify the default executor is reachable
scripts/doctor-executor.sh

# 3. Run the full demo (validate → place → run → emit artifacts)
scripts/demo.sh
```

After a successful run, artifacts appear under `artifacts/example-agent/`:

| File | Artifact kind |
|---|---|
| `validation-artifact.json` | `ValidationArtifact` |
| `placement-decision.json` | `PlacementDecision` |
| `placement-receipt.json` | `PlacementReceipt` |
| `run-artifact.json` | `RunArtifact` |
| `replay-artifact.json` | `ReplayArtifact` |

---

## Repository layout

```
agentplane/
├── bundles/              # Bundle definitions (bundle.json + vm.nix + smoke.sh)
│   └── example-agent/   # Reference bundle
├── docs/                 # Architecture, ADRs, integration guides, lifecycle docs
│   ├── adr/              # Architecture Decision Records
│   ├── integration/      # Per-system integration guides
│   ├── instrumentation/  # Receipt and instrumentation plans
│   └── runtime-governance/ # Control matrix integration
├── examples/             # Annotated example traces and reference assembler
│   └── receipts/
├── fleet/                # Executor inventory (fleet/inventory.json)
├── monitors/             # Generated control-matrix monitor bundles (reserved)
├── policy/               # Policy import lane + control-matrix bundles (reserved)
├── runners/              # Runner backends (qemu-local today; fleet later)
├── schemas/              # JSON Schemas for Bundle and all artifact kinds
├── scripts/              # CLI tools: validate, select-executor, emit artifacts
├── state/pointers/       # Current/previous bundle pointers (gitignored at runtime)
├── tests/                # Generated control-matrix test bundles (reserved)
└── tools/                # Developer utilities (receipt smoke test)
```

---

## Key concepts

- **Bundle** — The unit of deployment. Contains a VM module, rendered config, policy intent, smoke tests, and metadata. Defined by [schemas/bundle.schema.v0.1.json](schemas/bundle.schema.v0.1.json).
- **Executor** — A reachable Linux host (Lima VM today, fleet node later) listed in [fleet/inventory.json](fleet/inventory.json).
- **Evidence artifacts** — JSON files written to `spec.artifacts.outDir` proving the run happened and can be replayed.
- **Receipt** — A MAIPJ run receipt assembled from the normalized event stream produced across the full stack. See [docs/receipt-lifecycle.md](docs/receipt-lifecycle.md).

---

## Documentation map

| Topic | File |
|---|---|
| Architecture overview | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Bundle schema | [schemas/README.md](schemas/README.md) |
| Executor selection | [docs/executors.md](docs/executors.md) |
| System space / deployment topology | [docs/system-space.md](docs/system-space.md) |
| Receipt lifecycle | [docs/receipt-lifecycle.md](docs/receipt-lifecycle.md) |
| Sociosphere integration | [docs/integration/sociosphere.md](docs/integration/sociosphere.md) |
| State pointer model | [docs/state-pointers.md](docs/state-pointers.md) |
| Control matrix import | [policy/imports/control-matrix/README.md](policy/imports/control-matrix/README.md) |
| Architecture Decision Records | [docs/adr/README.md](docs/adr/README.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## Non-negotiables

- **No AGPL dependencies.** Every bundle must declare `metadata.licensePolicy.allowAGPL: false`. See [ADR-0001](docs/adr/0001-no-agpl-dependencies.md).
- **Evidence-forward execution.** Every run emits Validation, Placement, Run, and Replay artifacts.
- **Timeouts are bundle-owned policy.** Set via `spec.policy.maxRunSeconds` (5–3600 s).

---

## Relationship to the wider stack

agentplane is the execution control plane within a multi-repo stack:

```
sociosphere   →  agentplane  →  RunArtifact / ReplayArtifact / Receipt
slash-topics  →  agentplane  (context pack event stream)
human-digital-twin → agentplane  (policy/approval event stream)
TriTRPC       →  agentplane  (deterministic transport metadata)
```

See [docs/integration/sociosphere.md](docs/integration/sociosphere.md) and
[docs/sociosphere-bridge.md](docs/sociosphere-bridge.md) for the integration seam.
