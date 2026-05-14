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

## shir_governed_chain_job.py

Runs or projects the governed SHIR graph-ML manifest chain as an AgentPlane job fixture.

**Usage with checked-out dependencies:**

```bash
python tools/shir_governed_chain_job.py \
  --fabric-suite ../prophet-platform-fabric-mlops-ts-suite \
  --schema-ref ../semantic-serdes/schemas \
  --out-ref /tmp/agentplane-shir-chain \
  --trace-id trace.shir.governed_chain.local.001 \
  --policy-mode fail_closed
```

**What it does:**

1. Invokes the fabric-suite governed SHIR chain unless `--from-chain-receipt` is supplied.
2. Retains the chain stage artifacts under `--out-ref`.
3. Parses `chain_run_receipt.json`.
4. Projects the chain receipt into `agentplane_run_record.json`.
5. Maps policy outcomes and failure classes to AgentPlane states.

**Dependencies:** Python standard library only. The invoked fabric-suite chain may optionally validate against a semantic-serdes schema checkout.

**Related contract:** [docs/integration/shir-governed-chain.md](../docs/integration/shir-governed-chain.md)

---

## Related

- [examples/README.md](../examples/README.md) — Annotated examples including the example trace
- [docs/receipt-lifecycle.md](../docs/receipt-lifecycle.md) — Full receipt lifecycle documentation
- [docs/integration/shir-governed-chain.md](../docs/integration/shir-governed-chain.md) — SHIR governed chain AgentPlane job contract
- [examples/receipts/agentplane_live_receipt_emitter_reference.py](../examples/receipts/agentplane_live_receipt_emitter_reference.py) — Reference assembler (more featureful; suitable as a library)
