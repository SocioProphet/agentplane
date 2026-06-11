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

## Enrichment Twin (forward pointer)

The Enrichment Twin archetype (photo, media, document, per-asset analysis as a governed mission) is specified in `SocioProphet/ProCybernetica`:

- **Mission spec:** `ProCybernetica/docs/architecture/enrichment-twin-mission-spec.md`
- **GenesisSeed schema:** `ProCybernetica/schemas/genesis_seed.schema.json`
- **Enrichment claim hologram schema:** `ProCybernetica/schemas/enrichment_claim_hologram.schema.json`
- **Open decisions (owner call required before build):** `ProCybernetica/docs/adr/0002-enrichment-twin-open-decisions.md`

Agentplane is the target runtime for the Enrichment Twin. The integration surface is: receive a validated `seed:enrichment/photo-v1` bundle → bind organs → execute per-asset analysis → write claim holograms to memory-mesh → gate `GATED_HOST_UPDATE` with approval. The K3 twin bridge lifecycle (`INIT_SESSION → ... → TWIN_READY → GATED_HOST_UPDATE`) maps onto the existing agentplane bundle + executor + evidence chain.

Agent-buildable once: (1) the three open decisions in ADR-0002 have owner calls, (2) the placement scheduler locus-eligibility table is wired, and (3) `make validate` is green across prophet-platform, agentplane, memory-mesh, and model-router.
