# Agentplane Repository Map

## Cross-repo ownership

### Agentplane

Tenant-side control and execution responsibilities:

- gateway and remote ingress
- capability resolution and binding
- tenant worker runtime wrappers
- promotion and reversal runtime artifacts
- tenant-side evidence relay hooks

### Sociosphere

Device-local orchestration responsibilities:

- local supervisor
- local planning, retrieval, and execution precedence
- deterministic multi-repo orchestration

### TriTRPC

Deterministic transport and fixture responsibilities:

- method and envelope canon
- fixture vectors
- verification and repack invariants
- cross-language interoperability surface

### socioprophet-standards-storage

Shared contracts and measurement responsibilities:

- shared schemas
- benchmark definitions
- storage and interface standards
- governance and portability measurements

## Internal layout for Agentplane

### `schemas/`
Runtime artifact schemas and patch fragments.

### `docs/`
Architecture notes and slice definitions.

### `gateway/`
Tenant ingress for remote-eligible work.

### `capability-registry/`
Logical capability descriptors and runtime bindings.

### `worker-runtime/`
Tenant worker execution wrappers and contract adapters.

## First-slice sequence boundary

- `supervisor.v1.Session/Open` — local
- `supervisor.v1.Task/Plan` — local
- `policy.v1.Decision/Evaluate` — local first, tenant mirror optional
- `control.v1.Capability/Resolve` — tenant
- `worker.v1.Capability/Execute` — tenant
- `evidence.v1.Event/Append` — shared with local precedence
- `replay.v1.Cairn/Materialize` — local first
