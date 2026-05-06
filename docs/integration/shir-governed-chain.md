# SHIR Governed Chain AgentPlane Job v0.1

Status: draft handoff contract
Tracking issue: <https://github.com/SocioProphet/agentplane/issues/112>
Runtime pack home: `SocioProphet/prophet-platform-fabric-mlops-ts-suite`

## Purpose

This document defines the AgentPlane orchestration contract for the governed SHIR graph-ML manifest chain.

The runtime chain already exists in the fabric MLOps suite:

```text
rdf-to-shir -> shir-to-pyg -> semantic-leakage -> chain receipt
```

AgentPlane owns job orchestration: invoking the chain, retaining artifacts, interpreting policy outcomes, producing an AgentPlane run record, and fail-closing incomplete or unsafe runs.

## Job type

```yaml
job_type: shir.governed_chain.v0.1
```

## Inputs

| Field | Required | Description |
| --- | --- | --- |
| `input_ref` | yes | RDF-family artifact reference. v0.1 targets Turtle and may use the TopoLVM fixture. |
| `schema_ref` | yes | semantic-serdes schema checkout, version, or artifact reference. |
| `ontology_profile_ref` | yes | ontogenesis SHIR profile reference. |
| `fabric_suite_ref` | yes | checkout or container image containing the SHIR chain packs. |
| `out_ref` | yes | artifact retention directory, object prefix, or workspace path. |
| `prediction_cutoff` | no | optional timestamp for semantic-leakage temporal checks. |
| `policy_mode` | yes | one of `advisory`, `review_required`, or `fail_closed`. |
| `relation_strategy` | no | default `relation_node`. |
| `trace_id` | yes | AgentPlane trace identifier for receipt/run correlation. |

## Stage execution

AgentPlane should invoke the fabric suite chain runner as the first implementation path:

```bash
python packs/shir-governed-chain/tools/run_shir_chain.py \
  --input "$INPUT_REF" \
  --out-dir "$OUT_REF" \
  --schema-dir "$SCHEMA_REF"
```

The chain runner itself performs:

1. `rdf-to-shir`: compiles RDF/Turtle into SHIR candidate/assertion/receipt artifacts.
2. `shir-to-pyg`: lowers the SHIR assertion into a PyG-style manifest using relation-node preservation.
3. `projection-loss-report`: verifies no silent semantic flattening before graph-ML export.
4. `semantic-leakage`: checks manifest metadata and features for leakage markers.
5. `chain_run_receipt`: emits a semantic-serdes-compatible chain receipt.

## Required retained artifacts

AgentPlane must retain these artifacts when available:

```text
rdf-to-shir/candidate_assertion.json
rdf-to-shir/assertion.json
rdf-to-shir/receipt.json
shir-to-pyg/pyg_manifest.json
shir-to-pyg/projection_manifest.json
shir-to-pyg/projection_loss_report.json
shir-to-pyg/receipt.json
semantic-leakage/semantic_leakage_report.json
semantic-leakage/projection_loss_report.json
semantic-leakage/receipt.json
chain_run_receipt.json
chain_error.json, when present
```

## AgentPlane run states

| Condition | Recommended state |
| --- | --- |
| Chain succeeds and policy decision is `ALLOW` | `succeeded` |
| Chain succeeds but policy decision is `REVIEW_REQUIRED` | `requires_review` |
| Parse/schema/projection/leakage failure with `policy_mode: fail_closed` | `failed_closed` |
| Artifact retention failure | `failed_closed` |
| Replay hash mismatch | `failed_closed` |
| Human review pending | `requires_review` |

## Failure taxonomy

AgentPlane should distinguish these failure classes:

- `parse_failure`: RDF/Turtle parse or unsupported syntax error.
- `schema_validation_failure`: generated SHIR/projection/receipt artifact failed schema validation.
- `projection_loss_blocking`: projection-loss report contains blocking semantics loss.
- `semantic_leakage_blocking`: semantic-leakage report contains blocking leakage.
- `policy_denied`: policy outcome denies export/training/publication.
- `artifact_retention_failure`: artifact output could not be stored or sealed.
- `replay_mismatch`: replay hash or deterministic output mismatch.
- `chain_runtime_failure`: unexpected process/runtime failure.

Every failure should preserve the most specific error artifact available.

## AgentPlane run record projection

The AgentPlane run record should summarize:

```json
{
  "job_type": "shir.governed_chain.v0.1",
  "trace_id": "trace.shir.demo.001",
  "state": "succeeded",
  "policy_decision": "ALLOW",
  "input_ref": "packs/rdf-to-shir/fixtures/topolvm.ttl",
  "out_ref": "runs/shir/topolvm/001",
  "chain_receipt_ref": "runs/shir/topolvm/001/chain_run_receipt.json",
  "stage_receipts": {
    "rdf_to_shir": "shir.receipt.rdf_to_shir...",
    "shir_to_pyg": "shir.receipt.shir_to_pyg...",
    "semantic_leakage": "shir.receipt.semantic_leakage..."
  },
  "artifact_refs": [],
  "failure_class": null
}
```

The run record is not a replacement for the chain receipt. It is the AgentPlane control-plane view over the chain receipt and artifact set.

## Acceptance criteria

- AgentPlane has a stable `shir.governed_chain.v0.1` job contract.
- A fixture job points to the fabric suite TopoLVM chain.
- Chain artifacts are retained under a stable output prefix.
- Chain receipt is parsed and summarized into an AgentPlane run record.
- Blocking semantic leakage or projection loss maps to `requires_review` or `failed_closed` according to policy mode.
- Clean TopoLVM fixture maps to `succeeded` and policy decision `ALLOW`.
- No PyTorch, PyG, DGL, or LLM runtime is required for v0.1 orchestration.

## Completion estimate

After this contract, the remaining AgentPlane MVP work is a small fixture harness or adapter script. Estimated effort: 1-2 focused turns for a minimal implementation, or 3-5 turns if wired into an existing production runner instead of staying fixture-level.
