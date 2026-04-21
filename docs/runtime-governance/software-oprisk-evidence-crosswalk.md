# Software Operational Risk Evidence Crosswalk

## Purpose

This document maps the current `agentplane` evidence artifacts and execution phases to the software operational risk taxonomy and typed contract lane.

## Why this matters

The standards and contract layers now define:

- normalized operational incidents,
- normalized upstream watch items,
- scenario-run lineage,
- reserve/report envelopes,
- and analysis bundles.

`agentplane` is the execution control plane and needs a concrete crosswalk that explains how existing execution artifacts can participate in that chain.

## Current artifact crosswalk

| Execution phase | Existing artifact / concept | Primary oprisk interpretation | Expected downstream linkage |
|---|---|---|---|
| Validate | `ValidationArtifact` | Integrity / trust failure or prevented unsafe execution | can reference incident or watch items that caused validation denial or rewrite |
| Place | `PlacementDecision` | Concentration / common-mode exposure and execution-surface choice | can carry upstream drift or provider-state context influencing placement |
| Run | `RunArtifact` | Outage, degradation, recovery, or control effectiveness at execution time | can anchor degraded-run evidence and observed service impact |
| Replay | `ReplayArtifact` | Recovery, reproducibility, and incident investigation evidence | can support backtesting against outage corpus and scenario-run lineage |
| Promote | `PromotionArtifact` | Change-management / release execution risk | can tie to upstream drift and execution/process failures |
| Reverse | `ReversalArtifact` | Recovery / rollback control evidence | can support duration and severity reduction narratives |
| Session | `SessionArtifact` / `SessionReceipt` | End-to-end governed execution outcome | can reference scenario-run and reserve/report outputs for governed reviews |

## Event family mapping

| Oprisk event family | Agentplane execution implication |
|---|---|
| `execution_process_failure` | failed validation, bad placement, broken promotion, incorrect reversal, failed orchestration |
| `system_platform_disruption` | executor unreachable, backing service degraded, runtime failure during execution |
| `supply_chain_upstream_failure` | dependency or upstream package/registry/provider conditions affecting bundle safety or execution viability |
| `integrity_trust_failure` | invalid bundle, bad provenance, policy denial, unsafe execution surface |
| `concentration_common_mode_failure` | placement or run constrained by shared provider / executor concentration |
| `upstream_drift_integration_misalignment` | execution blocked or degraded because live upstream moved beyond validated assumptions |

## Minimal receipt linkage guidance

The first implementation step does **not** require a brand-new runtime artifact family.
Instead, existing artifacts SHOULD be able to reference:

- `SoftwareOperationalIncident` IDs,
- `UpstreamWatchItem` IDs,
- `SoftwareOperationalScenarioRun` IDs,
- `ReserveScenarioReport` IDs,
- and `SoftwareOperationalAnalysisBundle` IDs,

when those objects materially influenced execution decisions or evidence review.

## Immediate backlog

1. Add example receipt linkage showing execution evidence joined to typed operational-risk objects.  
2. Decide whether references live in existing artifacts or in a companion receipt overlay.  
3. Add at least one degraded-run example tied to an upstream watch item and one rollback example tied to a recovery narrative.
