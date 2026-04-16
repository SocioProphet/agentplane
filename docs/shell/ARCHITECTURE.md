# Architecture (re-synthesis)

## The system, in one sentence
A **contracts-first Knowledge Agent** emits verifiable artifacts (OCR/NLP/KG/provenance) that an **Agentplane Shell** renders, while an **immutable Linux OS** ensures deterministic updates, rollback, and least-privilege execution.

## Three planes
1) **Artifact plane (truth)**
- Immutable, content-addressed outputs: docs, pages, images, OCR text, NLP extractions, KG TSVs.
- Every record is keyed by SHA-256 and carries provenance fields.

2) **Execution plane (how truth is made)**
- Rootless containers + user-scoped systemd tasks run:
  - extract images
  - OCR images
  - NLP pages
  - export KGTK/CSKG
  - write ledgers/meta

3) **Rendering plane (how humans see truth)**
- UI shells read *only* the contracts. They do not invent data.
- Screens are modules over the same artifact set:
  - Inbox → doc inventory
  - Doc Detail → page preview
  - OCR Queue → images_ocr
  - NLP Explorer → page_jsonl
  - Graph → kgtk_* 
  - Ledger → run ledger + meta
  - OS Status/Updates/Security → host posture view

## Security baseline
- rootless runtime
- `cap-drop=ALL`
- `no-new-privileges`
- seccomp allowlist
- network disabled by default for ingestion

## Immutable OS binding
- rpm-ostree / MicroOS transactional updates
- Nix generations
- rollback as standard response to failed health checks

## Why contracts-first matters
- contracts are the stable API between *agent* and *UI*
- we can iterate on implementation without breaking the UX
- provenance can be verified independent of rendering
