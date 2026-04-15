# Architecture

agentplane is an evidence-forward execution control plane.  
Its job is to take a validated **Bundle**, select an **Executor**, run the bundle, and emit a tamper-evident evidence chain that supports deterministic replay and governed benchmarking.

---

## Design principles

1. **Contract-first.** The runner interface (`run / smoke / promote / rollback / status / stop`) is defined before any backend is implemented. Backends are pluggable.
2. **Evidence-forward.** Every run produces artifacts (Validation, Placement, Run, Replay). No silent runs.
3. **Bundle owns policy.** Timeouts, lane (staging/prod), human-gate requirements, and policy pack references live inside the bundle's `spec.policy` block — not in the runner or the executor.
4. **Executor discovery is layered.** An explicit `spec.executor.ref` in the bundle overrides the fleet inventory, which overrides the host Nix builder list. This precedence is intentional and documented in [docs/executors.md](docs/executors.md).
5. **No AGPL.** Hard-enforced at validation time. See [ADR-0001](docs/adr/0001-no-agpl-dependencies.md).
6. **Open-source only.** Matches the MIT license of this repo.

---

## Execution lifecycle

```
┌─────────────┐     validate      ┌───────────────────┐
│  Bundle     │ ───────────────►  │ ValidationArtifact│
│  (bundle.   │                   └───────────────────┘
│   json +    │     place         ┌───────────────────┐
│   vm.nix +  │ ───────────────►  │ PlacementDecision │
│   smoke.sh) │                   │ PlacementReceipt  │
└─────────────┘                   └───────────────────┘
       │           run             ┌───────────────────┐
       └─────────────────────────► │ RunArtifact       │
                                   └───────────────────┘
                   seal             ┌───────────────────┐
              ──────────────────►   │ ReplayArtifact    │
                                    └───────────────────┘
                   assemble          ┌────────────────────┐
              ──────────────────►    │ MAIPJ Run Receipt  │
                                     └────────────────────┘
```

All artifacts are written to `spec.artifacts.outDir` inside the bundle. See [schemas/README.md](schemas/README.md) for the JSON Schema for each artifact kind.

---

## Directory layout

```
agentplane/
├── bundles/                 Bundle definitions
│   └── example-agent/       Reference bundle (bundle.json, vm.nix, smoke.sh)
│
├── docs/                    Documentation
│   ├── adr/                 Architecture Decision Records
│   ├── integration/         Per-system integration guides
│   ├── instrumentation/     Receipt and instrumentation plans
│   └── runtime-governance/  Control-matrix integration plan
│
├── examples/                Annotated example traces and reference assembler
│   └── receipts/
│
├── fleet/                   Executor inventory
│   └── inventory.json       List of executors + default
│
├── monitors/                Reserved: generated control-matrix monitor bundles
│
├── policy/                  Policy import lane
│   └── imports/control-matrix/  Control-matrix bundle import manifest
│
├── runners/                 Runner backends
│   └── qemu-local.sh        Current backend (lima-process + QEMU paths)
│
├── schemas/                 JSON Schemas for Bundle and all artifact kinds
│
├── scripts/                 Operator CLI tools
│   ├── validate_bundle.py   Validates bundle + emits ValidationArtifact
│   ├── select-executor.py   Chooses executor + emits PlacementDecision (stdout)
│   ├── emit_run_artifact.py Emits RunArtifact from run outcome
│   ├── emit_replay_artifact.py  Emits ReplayArtifact
│   ├── demo.sh              Full end-to-end local demo
│   ├── doctor.sh            Preflight: checks Nix builders
│   ├── doctor-executor.sh   Preflight: probes all fleet executors
│   ├── hygiene.sh           Syntax checks (bash -n, py_compile)
│   └── pr.sh                Branch + commit + push + open PR
│
├── state/pointers/          Runtime pointer files (gitignored)
│   ├── current-staging      Points to currently active staging bundle dir
│   ├── current-prod         Points to currently active prod bundle dir
│   └── previous-good        Points to last known-good prod bundle dir
│
├── tests/                   Reserved: generated control-matrix test bundles
│
└── tools/                   Developer utilities
    └── receipt_smoke_test.py  Validates a trace file and assembles a receipt
```

---

## Component interactions

### Bundle

The central artifact. A bundle is a directory containing:

| File | Role |
|---|---|
| `bundle.json` | Manifest: metadata, policy, executor hint, artifact dir, smoke script ref, VM spec |
| `vm.nix` | NixOS module defining the guest environment |
| `smoke.sh` | Smoke test script (runs on host or inside guest) |

The bundle schema is [schemas/bundle.schema.v0.1.json](schemas/bundle.schema.v0.1.json).  
Additional agent-runtime fields are staged in [schemas/bundle.schema.patch.json](schemas/bundle.schema.patch.json).

### Fleet inventory (`fleet/inventory.json`)

Lists known executor nodes. Each entry has a name, SSH ref, and capability flags (`os`, `arch`, `kvm`).  
`defaultExecutor` names the fallback when a bundle does not pin an executor.

### Runner backends

The runner interface is defined in [runners/runner.md](runners/runner.md).  
`runners/qemu-local.sh` is the only current implementation. It supports two execution paths:

- **`lima-process`** — Syncs the repo to a Lima VM and runs the smoke script inside it. Used when the executor has `kvm: false` (TCG-only, avoids nested QEMU).
- **`qemu`** — Builds a full NixOS VM via `nix build`, then runs it with `QEMU_OPTS` to mount the artifact directory via virtio-9p.

The active path is chosen by inspecting `spec.vm.backendIntent` and the executor's `caps.kvm`.

### State pointer model

`state/pointers/` contains three plain-text files. See [docs/state-pointers.md](docs/state-pointers.md).

### Policy import lane

`policy/imports/control-matrix/` is a reserved import lane for Agentic Control Matrix bundles sourced from `SocioProphet/socioprophet-standards-storage`. Compiled bundles are not yet present. See the [import README](policy/imports/control-matrix/README.md) and [docs/runtime-governance/control-matrix-integration.md](docs/runtime-governance/control-matrix-integration.md).

---

## Multi-repo context

agentplane is the execution control plane within a larger stack:

```
┌────────────────┐  workspace artifacts  ┌────────────────────┐
│  sociosphere   │ ─────────────────────► │                    │
├────────────────┤  context pack events  │                    │
│  slash-topics  │ ─────────────────────► │   agentplane       │
├────────────────┤  policy/approval evts │                    │
│ human-digital- │ ─────────────────────► │  (validate →       │
│    twin        │                        │   place → run →    │
├────────────────┤  transport metadata   │   evidence →       │
│   TriTRPC      │ ─────────────────────► │   receipt)         │
├────────────────┤  normative schemas    │                    │
│ socioprophet-  │ ─────────────────────► │                    │
│ standards-     │                        └────────────────────┘
│   storage      │
└────────────────┘
```

Responsibility boundaries:

| Concern | Owner |
|---|---|
| Execution control plane, receipt assembly | `agentplane` |
| Workspace manifest and lock | `sociosphere` |
| Governed context packs | `slash-topics` |
| Policy evaluation and human approval | `human-digital-twin` |
| Deterministic transport | `TriTRPC` |
| Normative schemas and benchmark rubrics | `socioprophet-standards-storage` |

The integration seam between `sociosphere` and `agentplane` is described in [docs/sociosphere-bridge.md](docs/sociosphere-bridge.md). See [docs/integration/sociosphere.md](docs/integration/sociosphere.md) for a step-by-step guide.

---

## Evolution roadmap (system-space)

See [docs/system-space.md](docs/system-space.md) for the full enterprise alignment plan.

| Phase | Description |
|---|---|
| **Now** | Local-first: Lima VM as the single fleet node; `lima-process` backend |
| **Near-term** | Fedora Silverblue / Atomic Desktop as the control-plane host |
| **Fleet nodes** | Fedora CoreOS + Ignition; real executor mesh; fleet inventory grows |
| **Image-native** | `bootc` / OCI-based OS delivery; pointer swaps become digest swaps |
