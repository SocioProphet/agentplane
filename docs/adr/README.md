# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for agentplane.

ADRs capture significant design decisions, their context, the options considered, and the rationale for the choice made. Once an ADR is accepted it is immutable. If a decision is reversed or superseded, the original ADR is marked with a `Status: Superseded by ADR-XXXX` note and a new ADR is added.

---

## Index

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](0001-no-agpl-dependencies.md) | No AGPL dependencies | Accepted |
| [ADR-0002](0002-agentplane-owns-receipt.md) | agentplane owns the MAIPJ run receipt | Accepted |
| [ADR-0003](0003-sociosphere-owns-workspace-truth.md) | sociosphere owns workspace truth | Accepted |
| [ADR-0004](0004-gakw-first-live-benchmark.md) | GAKW as the first live benchmark path | Accepted |
| [ADR-0005](0005-lima-process-kvm-fallback.md) | lima-process fallback when KVM is absent | Accepted |
| [ADR-0006](0006-narrow-sociosphere-seam.md) | Intentionally narrow sociosphere ↔ agentplane seam | Accepted |
| [ADR-0007](0007-single-writer-receipt-field-ownership.md) | Single-writer field ownership for receipt assembly | Accepted |

---

## Template

```markdown
# ADR-XXXX: <title>

Date: YYYY-MM-DD  
Status: Proposed | Accepted | Superseded by ADR-XXXX

## Context

<What is the situation that prompted this decision?>

## Decision

<What was decided?>

## Consequences

<What are the positive and negative consequences of this decision?>
```
