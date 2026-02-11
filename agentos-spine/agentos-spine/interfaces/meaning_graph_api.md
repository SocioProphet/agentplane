# MeaningGraphAPI (v0.1)

Goal: represent agent/claim graphs (identity + assertions + relations) with portability.

## Required operations

- `put_claim(agent_id, claim, provenance) -> claim_id`
- `link(src_claim_id, rel, dst_claim_id, provenance) -> link_id`
- `query(query_spec) -> results`
- `export_snapshot() -> snapshot_ref`
- `import_snapshot(snapshot_ref)`

## Providers

- AD4M (current provider)
- MG-Core (planned permissive replacement)
