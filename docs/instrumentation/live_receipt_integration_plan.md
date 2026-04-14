# Live Receipt Integration Plan v0.1
## SocioProphet AI+HW+State stack

> **Status: Plan document — phases not yet complete.**  
> Phase 0 (schema and event freeze) is in progress. The `maipj-run-receipt.schema.json` schema
> is pending publication in `SocioProphet/socioprophet-standards-storage`. Phases 1–3 have not
> started. The reference assembler and example trace are available in `examples/receipts/`.  
> See [docs/receipt-lifecycle.md](../receipt-lifecycle.md) for the current working specification.

### Purpose
This plan turns the MAIPJ doctrine and GAKW benchmark family into a first live integration path.
The target is one real governed execution path that emits one valid MAIPJ run receipt with
traceable provenance, replay support, policy state, and end-to-end energy accounting.

This is intentionally **not** a grand unified everything-spec. It is the minimum executable
bridge from doctrine to instrumentation.

### Integration target
**Target benchmark family:** GAKW (Governed Assistive Knowledge Work)

**Target first live path:**
1. A workspace is resolved and locked.
2. Context packs are selected and fetched.
3. A governed execution plan is built.
4. The request is placed on a local / edge / hybrid / cloud target.
5. The model runs.
6. Policy checks and optional human approval are applied.
7. Evidence and replay artifacts are sealed.
8. A MAIPJ run receipt is emitted.

### Why this path first
This path forces all critical layers to participate:
- workspace / manifest state,
- governed context,
- deterministic transport,
- execution control plane,
- policy and approval,
- evidence / replay,
- mission-weighted utility accounting.

It is therefore a better first benchmark path than a bare model invocation.

## Repo-by-repo responsibility map

### `agentplane`
**Role:** control plane, planner, executor, evidence emitter, receipt owner.

**Must provide**
- trace and span IDs for every governed execution,
- placement decision record,
- model/runtime/compiler identifiers,
- timing boundaries for bundle→validate→run→evidence→replay stages,
- raw energy accounting hooks or imported estimates,
- final receipt assembly and signing hook,
- replay manifest identifier.

**Emission points**
- `plan.created`
- `placement.selected`
- `run.started`
- `run.completed`
- `evidence.sealed`
- `receipt.emitted`

### `sociosphere`
**Role:** workspace/filesystem state and composition authority.

**Must provide**
- workspace manifest ID,
- workspace lock digest,
- benchmark family / case binding,
- execution policy reference,
- dependency and pack references,
- reproducibility metadata needed for replay.

**Emission points**
- `workspace.resolved`
- `workspace.locked`
- `workspace.materialized`

### `slash-topics`
**Role:** governed context plane.

**Must provide**
- context pack IDs,
- content digests,
- locality class,
- byte counts,
- cache hit/miss counts,
- remote fetch counts,
- retrieval provenance per pack.

**Emission points**
- `context.pack.selected`
- `context.pack.fetched`
- `context.cache.hit`
- `context.cache.miss`

### `TriTRPC`
**Role:** deterministic transport and envelope discipline.

**Must provide**
- request / response envelope IDs,
- authenticated transport metadata,
- deterministic serialization hash,
- retry / timeout / failure semantics,
- optional transport-level latency split.

**Emission points**
- `rpc.request.sent`
- `rpc.response.received`
- `rpc.retry`
- `rpc.fail`

### `human-digital-twin`
**Role:** consent, approval, policy, human-facing trust membrane.

**Must provide**
- policy bundle ID,
- approval requirement decision,
- approval event / consent state reference,
- trust-class and risk-class mapping,
- attestation or signature references where applicable.

**Emission points**
- `policy.evaluated`
- `approval.requested`
- `approval.granted`
- `approval.denied`

### `socioprophet-standards-storage`
**Role:** normative schemas, benchmark rules, scoring rubrics.

**Must provide**
- receipt schema version,
- utility rubric version,
- benchmark family and casebook version,
- accounting-boundary definitions,
- mission-weight policy definitions for benchmark scenarios.

**Emission points**
- no runtime emission required;
- version identifiers must be imported into the emitted receipt.

### `socioprophet`
**Role:** mission/application surface and benchmark workload owner.

**Must provide**
- real task-family definitions,
- business/mission outcome mapping,
- application-level quality scoring,
- operator-visible failure classes.

**Emission points**
- `task.opened`
- `task.completed`
- `task.failed`

### Optional / adjacent repos
#### `gaia-world-model`
Use when the execution path depends on provenance-pinned world-state or constrained action context.

#### `cairnpath-mesh`
Use when execution receipts must bind into multi-step DAG / path evidence beyond a single run.

## Canonical receipt field ownership

The field ownership model should be single-writer wherever possible.

| Receipt field block | Primary owner | Secondary contributor |
|---|---|---|
| `receipt_id`, `trace_id`, `span_id`, `timestamp` | `agentplane` | `TriTRPC` |
| `task.*` | `socioprophet` | `socioprophet-standards-storage` |
| `placement.*` | `agentplane` | infrastructure adapters |
| `model_runtime.*` | `agentplane` | runtime/compiler adapters |
| `context.pack_*`, `context.locality_*`, `context.cache_*` | `slash-topics` | `sociosphere` |
| `context.policy_bundle_id` | `human-digital-twin` | `sociosphere` |
| `energy_j.*` | `agentplane` | hardware/runtime meters |
| `outcome.quality` | application scorer | `socioprophet` |
| `outcome.policy_pass`, `outcome.human_approved` | `human-digital-twin` | `agentplane` |
| `outcome.replayable` | `agentplane` | `sociosphere` |
| `evidence.*` | `agentplane` | `human-digital-twin` |
| `replay.*` | `agentplane` | `sociosphere` |

## First live path design

### Proposed case
`gakw_hybrid_warm_answer`

This is the best first live case because it:
- uses governed context packs,
- crosses local and remote boundaries,
- can require human approval,
- is replayable,
- is not blocked on exotic hardware.

### Minimal execution sequence
1. `sociosphere` resolves a workspace manifest and lock.
2. The benchmark case reference is loaded from `socioprophet-standards-storage`.
3. `slash-topics` selects and materializes the required context packs.
4. `human-digital-twin` resolves the applicable policy bundle.
5. `agentplane` plans placement and launches execution.
6. `TriTRPC` carries deterministic transport for remote or hybrid legs.
7. The model runtime returns output plus runtime metadata.
8. `human-digital-twin` evaluates policy / approval requirements.
9. `agentplane` seals evidence, writes replay manifest, and emits the receipt.

## Event contract

All events should be normalized into a single envelope before receipt assembly.

### Required envelope
```json
{
  "event_id": "evt_...",
  "trace_id": "trace_...",
  "span_id": "span_...",
  "parent_span_id": "span_...",
  "event_type": "workspace.locked",
  "ts": "2026-04-05T00:00:00Z",
  "producer": "sociosphere",
  "payload": {}
}
```

### Event type set for the first path
- `workspace.resolved`
- `workspace.locked`
- `context.pack.selected`
- `context.pack.fetched`
- `policy.evaluated`
- `placement.selected`
- `run.started`
- `run.completed`
- `approval.requested`
- `approval.granted`
- `evidence.sealed`
- `receipt.emitted`

## Energy accounting boundary

The accounting boundary for the first live path is:

**device + host + allocated network + storage + cooling-adjusted site factor**

Included
- inference energy,
- data movement energy,
- network energy,
- storage IO energy,
- control-plane energy,
- idle allocation,
- cooling-adjusted site factor.

Excluded for the first live path
- training amortization beyond static model-level estimate,
- embodied hardware lifecycle,
- upstream shared-dataset ingestion unrelated to the run.

### Metering strategy
- Prefer direct device / host counters where available.
- Fall back to estimator models with explicit `estimation_model`.
- Never omit a category silently; if unknown, set an estimate and mark the estimate source.

## Minimal implementation tasks

### Phase 0 — schema and event freeze
- Freeze `maipj-run-receipt.schema.json`.
- Freeze event names for the first path.
- Freeze the accounting-boundary string.
- Freeze the benchmark family and casebook version.

### Phase 1 — emit raw events
- `sociosphere` emits workspace events.
- `slash-topics` emits context selection/fetch/cache events.
- `human-digital-twin` emits policy/approval events.
- `agentplane` emits placement/run/evidence/receipt events.
- `TriTRPC` emits transport timing and retry metadata.

### Phase 2 — assemble receipt
- Add a receipt builder library in `agentplane`.
- Join the event stream by `trace_id`.
- Validate against the JSON Schema.
- Reject receipt emission if required fields are missing.

### Phase 3 — baseline report
- Run at least 10 executions of one case.
- Emit receipts.
- Run the reference harness.
- Produce CSV + markdown report + plots.

## Acceptance criteria for v0.1
A v0.1 live path is complete when all of the following are true:
1. At least one real execution emits a schema-valid receipt.
2. The receipt energy components sum exactly to `energy_j.total`.
3. The receipt contains at least one real context pack ID and digest.
4. The receipt contains a real policy bundle ID.
5. The receipt contains a real replay manifest ID.
6. The receipt passes through the reference harness without modification.
7. A baseline MAIPJ report is generated from live receipts.

## Recommended repo file destinations

### `agentplane`
- `/docs/instrumentation/live_receipt_integration_plan.md`
- `/pkg/receipt_builder/`
- `/schemas/events/agentplane-events.json`

### `sociosphere`
- `/spec/workspace/manifest_extensions.yaml`
- `/schemas/events/workspace-events.json`

### `slash-topics`
- `/schemas/events/context-events.json`
- `/spec/topicpack/provenance_and_locality.md`

### `TriTRPC`
- `/spec/transport/receipt_binding.md`

### `human-digital-twin`
- `/spec/policy/approval_event_schema.json`
- `/spec/evidence/consent_attestation_binding.md`

### `socioprophet-standards-storage`
- `/benchmarks/gakw/`
- `/schemas/maipj-run-receipt.schema.json`
- `/rubrics/gakw-utility-v0.1.json`

## Risks and traps

### 1. Fake energy precision
Do not emit six decimal places of fantasy when the meter is actually estimated from coarse counters.

### 2. Double counting
Network and data-movement energy can easily get counted twice if host + NIC + fabric models overlap.

### 3. Evidence theater
A receipt with hashes but no retrievable replay manifest is just cosplay with more punctuation.

### 4. Split authority
If both `sociosphere` and `agentplane` think they own workspace truth, the run receipt will rot.

### 5. Silent policy drift
Policy bundle IDs must be explicit and versioned or benchmark results will become incomparable.

## Decision log
- First live path uses GAKW, not robotics or batch training.
- Receipt owner is `agentplane`.
- Workspace truth is `sociosphere`.
- Context truth is `slash-topics`.
- Policy truth is `human-digital-twin`.
- Deterministic transport truth is `TriTRPC`.
- Normative schema truth is `socioprophet-standards-storage`.

## Next step after v0.1
After one live path works, run an **A/B placement comparison**:
- same case,
- same context pack family,
- same utility rubric,
- different placement: edge vs cloud vs hybrid.

That is the first honest MAIPJ comparison worth taking seriously.