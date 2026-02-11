# MemoryAPI (v0.1)

Goal: cross-session memory store for agents.

## Required operations

- `put(item: MemoryItem) -> id`
- `get(id) -> MemoryItem`
- `search(query, filters) -> MemoryItem[]`
- `export() -> ArchiveRef`
- `import(ArchiveRef)`

## Providers

- Mem0 (primary)
- (optional) local sqlite/jsonl for offline mode
