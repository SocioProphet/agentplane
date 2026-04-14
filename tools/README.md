# tools

Developer utilities for agentplane.

---

## receipt_smoke_test.py

Validates a MAIPJ event trace and assembles a receipt from it.

**Usage:**

```bash
python tools/receipt_smoke_test.py examples/receipts/gakw_hybrid_warm_trace.example.json
```

**What it does:**

1. Loads the trace JSON file.
2. Checks that all 8 required event types are present.
3. Assembles a receipt from the event stream (sorted by timestamp).
4. Verifies that `energy_j.total` equals the sum of the component energy fields.
5. Prints the assembled receipt as formatted JSON.

**Required event types:**

```
workspace.locked
context.pack.selected
context.pack.fetched
policy.evaluated
placement.selected
run.started
run.completed
evidence.sealed
```

If any are missing, the tool exits with a non-zero status and prints the list of missing events.

**Dependencies:** Python standard library only (no third-party packages).

**When to run:** Run this tool whenever you modify `examples/receipts/` or add new example
traces to verify that receipt assembly still works correctly.

---

## Related

- [examples/README.md](../examples/README.md) — Annotated examples including the example trace
- [docs/receipt-lifecycle.md](../docs/receipt-lifecycle.md) — Full receipt lifecycle documentation
- [examples/receipts/agentplane_live_receipt_emitter_reference.py](../examples/receipts/agentplane_live_receipt_emitter_reference.py) — Reference assembler (more featureful; suitable as a library)
