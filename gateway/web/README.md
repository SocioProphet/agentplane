# Agentplane Shell

The **Agentplane Shell** is the control-surface UI for tenant-side execution evidence.

It renders the evidence and read models produced around the Agentplane lifecycle:

```
Bundle → Validate → Place → Run → Evidence → Replay
```

The shell is deliberately **contracts-first**. It reads stable artifact contracts rather than inventing a separate UI-only state model.

## Why this lives under `gateway/`

The shell is a tenant-facing control-plane surface for remote-eligible work, evidence inspection, replay visibility, graph export inspection, and immutable-host posture overlays. That makes it a natural extension of the `gateway/` surface rather than a detached application island.

## Module set

- Inbox
- Doc Detail
- OCR Queue
- NLP Explorer
- Graph
- Export Workbench
- Ledger
- OS Status
- Updates / Rollback
- Security Policies
- Search

## Contracts incubated here

- `contracts/interface_contracts.json`
- `contracts/alignment_matrix.csv`

These are the working contracts for the shell surface. Once stabilized, the ecosystem-wide versions should be promoted to:

- `SourceOS-Linux/sourceos-spec` for canonical machine-readable contract ownership
- `SocioProphet/socioprophet-standards-storage` for standards prose, measurement, and governance posture

## Samples

See `samples/` for contract-conforming examples that let the shell render without a live backend.

## Docs

- `../../docs/shell/README.md`
- `../../docs/shell/ARCHITECTURE.md`
- `../../docs/shell/UI_SPEC.md`
- `../../docs/shell/ROADMAP.md`
- `../../docs/shell/ALIGNMENT_SUMMARY.md`
- `../../docs/shell/COMPLIANCE_REPORT.md`
