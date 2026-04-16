# Software Operational Risk Alignment

## Purpose

This note records how `agentplane` aligns to the software operational risk governance pack proposed in `SocioProphet/socioprophet-standards-storage` PR #72.

## Why this repo is in scope

The current repository positioning already makes `agentplane` the execution control plane and evidence-producing runtime surface for governed bundle runs, replay, placement, promotion, reversal, and session artifacts.

That means `agentplane` is the correct downstream implementation owner for execution-plane implications of software operational risk, including:

- outage / degradation execution receipts;
- upstream-drift execution consequences;
- runtime evidence artifacts tied to failure, rollback, recovery, and replay;
- and policy-visible execution boundaries for critical service paths.

## Expected integration points

### 1. Artifact family expansion

The execution artifact family SHOULD be extended or crosswalked to support software operational risk concepts such as:

- outage receipt,
- degradation receipt,
- upstream drift receipt,
- recovery / restoration receipt,
- and dependency-path evidence references.

These MAY remain composed from existing artifact families if that preserves current runtime simplicity.

### 2. Critical service path mapping

Agentplane SHOULD identify the critical execution services it owns or materially influences, including at least:

- validate,
- place,
- run,
- replay,
- promote,
- reverse,
- and recover.

Each service path SHOULD be able to map to the normative taxonomy defined in the governance pack.

### 3. Runtime-governance linkage

Runtime governance docs and control-matrix integration SHOULD eventually reference:

- outage event classes,
- integrity / trust failures,
- common-mode execution dependencies,
- and upstream drift as an explicit execution risk driver.

### 4. Evidence forwarding

Where `sociosphere` or other automation lanes harvest outage or upstream-watch data, `agentplane` SHOULD be able to consume that context when execution policy or replay trust depends on it.

## Immediate backlog

1. Decide whether software operational risk uses new artifact schemas or a documented composition of existing artifacts.  
2. Add a service-path table mapping execution phases to outage / degradation / integrity event classes.  
3. Add at least one example receipt or example bundle demonstrating operational-risk evidence flow.  
4. Cross-reference the standards pack once PR #72 lands.
