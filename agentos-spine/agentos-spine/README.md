# AgentOS Spine

This repository is the **integration spine** for the SocioProphet / SourceOS ecosystem.

It is intentionally **contract-first**:

- **Standards and artifacts are authoritative** (git + AIWG artifacts)
- Tools integrate **only via stable interfaces** (adapters + contract tests)
- Higher-risk components (copyleft / source-available / proprietary / unclear license) are **boxed** behind
  service boundaries and can be replaced without rewriting the world.

## Quick start (local)

1) Put your downloaded archives in `_archives/`:

- `_archives/Archive.zip` (the spine bundle: SourceOS, TriTRPC, standards, etc.)
- optionally other repo zips you want to inspect

2) Extract + normalize the spine workspace:

```bash
python3 scripts/ingest_archives.py --archive _archives/Archive.zip
```

This creates `spine/` with normalized folder names (and strips `.git`, `.DS_Store`, `.venv`, `__pycache__`, `*.pyc`).

3) Validate hygiene + license posture:

```bash
python3 scripts/validate_spine.py
```

## Repo contents

- `registry/` — canonical tool/repo registry (license + lane + replacement posture)
- `interfaces/` — stable contracts (Executor, Orchestrator, BrowserOps, MemoryAPI, MeaningGraphAPI, etc.)
- `docs/` — rollout plan, guardrails, replacement strategy
- `scripts/` — ingestion + validation utilities (safe defaults)

## Non-goals

This repo is **not** a monorepo of all components. It is a control plane for:
- what we integrate,
- how we integrate it,
- and how we keep it swappable.
