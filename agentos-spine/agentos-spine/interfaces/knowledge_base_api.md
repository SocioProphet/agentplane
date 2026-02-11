# KnowledgeBaseAPI (v0.1)

Goal: durable project knowledge base (documents + semantic search), swappable.

## Required operations

- `ingest(doc, metadata) -> doc_id`
- `search(query, filters) -> hits`
- `get(doc_id) -> doc`
- `export_snapshot() -> snapshot_ref`
- `import_snapshot(snapshot_ref)`

## Providers

- Fortemi (evaluation / boxed)
- KB-Core (planned permissive replacement: pgvector/qdrant/etc.)
