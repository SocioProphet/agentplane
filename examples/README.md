# examples

Annotated examples for agentplane.

---

## receipts/

Example event traces and reference implementations for MAIPJ run receipt assembly.

| File | Description |
|---|---|
| [`gakw_hybrid_warm_trace.example.json`](receipts/gakw_hybrid_warm_trace.example.json) | Complete example event trace for the `gakw_hybrid_warm_answer` benchmark case. Contains all 8 required event types in sequence. |
| [`agentplane_live_receipt_emitter_reference.py`](receipts/agentplane_live_receipt_emitter_reference.py) | Reference receipt assembler. Reads a trace JSON from stdin, assembles a receipt, enforces required fields and the energy-sum invariant, and prints the assembled receipt. |

### Using the example trace

Assemble a receipt from the example trace using the smoke test tool:

```bash
python tools/receipt_smoke_test.py examples/receipts/gakw_hybrid_warm_trace.example.json
```

Or using the reference assembler directly:

```bash
python examples/receipts/agentplane_live_receipt_emitter_reference.py \
  < examples/receipts/gakw_hybrid_warm_trace.example.json
```

Both should produce a JSON receipt with all required fields populated and `energy_j.total`
equal to the sum of the component energy fields.

### About UNSET values

The example trace uses placeholder digests (`sha256:lock-example`, `sha256:pack01`, etc.).
In a real trace these would be actual SHA-256 digests of the referenced artifacts.

### Energy accounting note

The `run.completed` event payload in the example trace includes a `replay_j` field (value 3.0).
This field is recorded in the assembled receipt's `energy_j` block but is **excluded from
`energy_j.total`** by design — replay energy is infrastructure overhead, not the primary run
cost. See [docs/receipt-lifecycle.md](../docs/receipt-lifecycle.md#energy-accounting) for the
full accounting specification.

---

## Related documentation

- [docs/receipt-lifecycle.md](../docs/receipt-lifecycle.md) — Full lifecycle, event catalog, field ownership, energy rules
- [docs/integration/sociosphere.md](../docs/integration/sociosphere.md) — How to drive a run from a sociosphere workspace
- [tools/README.md](../tools/README.md) — Receipt smoke test and other developer utilities
