# Receipt Lifecycle

This document describes the full MAIPJ run receipt lifecycle in agentplane:
the events that drive it, the field ownership model, and the energy accounting rules.

For the multi-repo integration plan that defines the first live path, see
[docs/instrumentation/live_receipt_integration_plan.md](instrumentation/live_receipt_integration_plan.md).

---

## Overview

A MAIPJ run receipt is assembled from a normalized stream of events produced by all participating
subsystems during a single governed execution. `agentplane` is the receipt owner: it collects
the events, joins them by `trace_id`, validates the assembled receipt, and emits the final
record.

**Receipt assembly is fail-closed.** If any required event is missing, `agentplane` raises an
error and refuses to emit a partial receipt.

---

## Event lifecycle

Each event in the stream has the following envelope:

```json
{
  "event_id":      "evt_...",
  "trace_id":      "trace_...",
  "span_id":       "span_...",
  "parent_span_id":"span_...",
  "event_type":    "workspace.locked",
  "ts":            "2026-04-05T07:30:00Z",
  "producer":      "sociosphere",
  "payload":       {}
}
```

### Required events

The following eight event types **must** be present in every receipt trace.
If any are missing, receipt assembly fails.

| Event type | Producer | Purpose |
|---|---|---|
| `workspace.locked` | `sociosphere` | Task family, case ID, risk class, utility rubric version |
| `context.pack.selected` | `slash-topics` | Pack IDs, digests, policy bundle ID, locality class |
| `context.pack.fetched` | `slash-topics` | Byte counts, cache hit/miss rates |
| `policy.evaluated` | `human-digital-twin` | Policy pass/fail, approval requirement |
| `placement.selected` | `agentplane` | Site, executor, model/runtime identifiers |
| `run.started` | `agentplane` | Execution start timestamp |
| `run.completed` | `agentplane` | Energy breakdown, outcome quality metrics |
| `evidence.sealed` | `agentplane` | Input/output digests, evidence refs, replay manifest |

### Optional events

These events enrich the receipt but are not required for assembly:

| Event type | Producer | Purpose |
|---|---|---|
| `workspace.resolved` | `sociosphere` | Early workspace resolution confirmation |
| `workspace.materialized` | `sociosphere` | Workspace materialization confirmation |
| `context.cache.hit` | `slash-topics` | Per-pack cache hit detail |
| `context.cache.miss` | `slash-topics` | Per-pack cache miss detail |
| `approval.requested` | `human-digital-twin` | Human approval gate opened |
| `approval.granted` | `human-digital-twin` | Human approval received |
| `approval.denied` | `human-digital-twin` | Human approval denied |
| `rpc.request.sent` | `TriTRPC` | Transport envelope ID |
| `rpc.response.received` | `TriTRPC` | Transport latency, deterministic hash |
| `task.opened` | `socioprophet` | Application task opened |
| `task.completed` | `socioprophet` | Application task completed |
| `task.failed` | `socioprophet` | Application task failed |

---

## Assembly stages

Receipt assembly happens in the following order (events sorted by `ts` within each stage):

```
1. workspace.locked       →  receipt.task, receipt._workspace
2. context.pack.selected  →  receipt.context (pack IDs, digests, policy, locality)
3. context.pack.fetched   →  receipt.context (byte counts, cache stats)
4. policy.evaluated       →  receipt.outcome (policy_pass, human_approved)
5. placement.selected     →  receipt.placement, receipt.model_runtime
6. run.started            →  (timestamp anchor)
7. run.completed          →  receipt.energy_j, receipt.outcome (quality, latency, replayable)
8. evidence.sealed        →  receipt.evidence, receipt.replay
```

The reference implementation is in
[examples/receipts/agentplane_live_receipt_emitter_reference.py](../examples/receipts/agentplane_live_receipt_emitter_reference.py).

---

## Field ownership

Each receipt field block has exactly one primary owner (see [ADR-0007](adr/0007-single-writer-receipt-field-ownership.md)):

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

---

## Energy accounting

### Invariant

```
energy_j.total = train_amortized + inference + data_move + network
               + storage + control + idle + cooling_adjusted
```

`replay_j` is recorded in the energy block but **excluded from the total** — it represents
replay-infrastructure cost, not the primary run cost. See
[examples/receipts/agentplane_live_receipt_emitter_reference.py](../examples/receipts/agentplane_live_receipt_emitter_reference.py),
lines 141–152, for the canonical summation.

This invariant is enforced by `ReceiptBuilder.finalize()`. A receipt where the sum does not
match will be rejected.

### Accounting boundary

The accounting boundary for the first live path is:

```
device + host + allocated-network + storage + cooling-adjusted-site-factor
```

Included:
- inference energy
- data movement energy
- network energy
- storage IO energy
- control-plane energy
- idle allocation
- cooling-adjusted site factor

Excluded (first live path):
- training amortization beyond static model-level estimate
- embodied hardware lifecycle
- upstream shared-dataset ingestion unrelated to the run

### Metering strategy

- Prefer direct device/host counters where available.
- Fall back to estimator models with an explicit `estimation_model` string.
- Never omit a category silently. If unknown, set an estimate and mark the source.

---

## Required receipt fields

A valid receipt must contain all of the following top-level keys:

```
receipt_id, trace_id, span_id, timestamp,
task, context, placement, model_runtime,
energy_j, outcome, evidence, replay
```

### energy_j required sub-fields

```
train_amortized, inference, data_move, network, storage,
control, idle, cooling_adjusted, total,
accounting_boundary, estimation_model
```

### outcome required sub-fields

```
quality, calibration, robustness, latency_ms, replayable,
policy_pass, human_approved
```

---

## Missing schema note

The normative `maipj-run-receipt.schema.json` schema is defined in
`SocioProphet/socioprophet-standards-storage`. It must be frozen before the first live receipt
can be emitted (Phase 0 of the integration plan). Until that schema is available and imported,
use the reference assembler and the field requirements above as the working specification.

The `receiptSchemaVersion` field is staged in
[schemas/bundle.schema.patch.json](../schemas/bundle.schema.patch.json) and should be set to
the frozen schema version once it is published.

---

## Example trace

A complete annotated example trace is in
[examples/receipts/gakw_hybrid_warm_trace.example.json](../examples/receipts/gakw_hybrid_warm_trace.example.json).

To assemble a receipt from it:

```bash
python tools/receipt_smoke_test.py examples/receipts/gakw_hybrid_warm_trace.example.json
```

Or using the reference assembler directly:

```bash
python examples/receipts/agentplane_live_receipt_emitter_reference.py \
  < examples/receipts/gakw_hybrid_warm_trace.example.json
```
