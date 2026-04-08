# ADR-0007: Single-writer field ownership for receipt assembly

Date: 2026-04-05  
Status: Accepted

## Context

A MAIPJ run receipt aggregates contributions from multiple subsystems. If two subsystems both
write to the same receipt field, the result is ambiguous and potentially inconsistent.

Two models were considered:

1. **Consensus model** — Any subsystem can write any field; conflicts are resolved by a merge
   policy.
2. **Single-writer model** — Each receipt field block has exactly one primary writer. A
   secondary contributor may supply a value only if the primary is unavailable.

## Decision

The single-writer model is adopted. Each receipt field block has a designated primary owner and
an optional secondary contributor. The primary owner is responsible for the correctness of its
fields; secondary contributors supply supplemental data only.

The ownership table is maintained in
[docs/receipt-lifecycle.md](../receipt-lifecycle.md#field-ownership).

Key assignments:

| Receipt field block | Primary owner |
|---|---|
| `receipt_id`, `trace_id`, `span_id`, `timestamp` | `agentplane` |
| `task.*` | `socioprophet` |
| `placement.*` | `agentplane` |
| `model_runtime.*` | `agentplane` |
| `context.*` | `slash-topics` |
| `energy_j.*` | `agentplane` |
| `outcome.quality` | application scorer |
| `outcome.policy_pass`, `outcome.human_approved` | `human-digital-twin` |
| `outcome.replayable` | `agentplane` |
| `evidence.*` | `agentplane` |
| `replay.*` | `agentplane` |

## Consequences

- **Positive:** No ambiguity about who is responsible for a field being correct.
- **Positive:** Makes receipt validation deterministic: if the primary owner did not emit the
  field, the receipt is incomplete.
- **Positive:** Simplifies debugging: a wrong field value has exactly one place to fix.
- **Negative:** If the primary owner for a field is unavailable (e.g., `socioprophet` does not
  emit a `task.*` event), the receipt cannot be finalized. This is intentional — a partial
  receipt is not emitted.
- **Negative:** The ownership table must be kept up to date as the receipt schema evolves.
