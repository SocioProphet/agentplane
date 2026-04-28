# docs

Documentation for agentplane.

---

## Index

| File / Directory | Contents |
|---|---|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | High-level architecture: lifecycle, directory layout, component interactions, multi-repo context |
| [adr/](adr/README.md) | Architecture Decision Records (ADRs) |
| [executors.md](executors.md) | Executor selection precedence and capability flags |
| [system-space.md](system-space.md) | Enterprise deployment topology: local-first → fleet → bootc |
| [sociosphere-bridge.md](sociosphere-bridge.md) | Sociosphere ↔ agentplane seam: artifact types, env vars, run order |
| [receipt-lifecycle.md](receipt-lifecycle.md) | Full MAIPJ run receipt lifecycle: events, field ownership, energy accounting |
| [state-pointers.md](state-pointers.md) | `state/pointers/` model: current-staging, current-prod, previous-good |
| [integration/](integration/README.md) | Per-system integration guides |
| [instrumentation/live_receipt_integration_plan.md](instrumentation/live_receipt_integration_plan.md) | Live receipt integration plan v0.1 (plan document) |
| [runtime-governance/control-matrix-integration.md](runtime-governance/control-matrix-integration.md) | Control matrix runtime binding plan (plan document) |

---

## Conventions

- **ADRs** record significant design decisions. Once accepted they are immutable; superseded ADRs are marked `Status: Superseded by ADR-XXXX`.
- **Plan documents** (suffixed `_plan.md` or titled "plan") are forward-looking and may not reflect current implementation. Check the implementation status note at the top of each plan file.
- **Reference documents** (this index, executors.md, sociosphere-bridge.md, receipt-lifecycle.md, state-pointers.md) should stay in sync with the code.
