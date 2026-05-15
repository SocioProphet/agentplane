# Agentic Control Plane Reference Architecture v0

Status: Informative reference note.

This document captures the current AgentPlane control-plane reference architecture in text form. It is intentionally informative rather than normative. Normative behavior remains in versioned schemas, runtime validators, policy-fabric contracts, and executable gates.

## Why this exists

The current AgentPlane work has converged on a layered control-plane model:

- typed work intake and planning;
- policy-governed execution eligibility;
- evidence-producing runners;
- postcondition and divergence recording;
- review and merge gates for agent-produced changes;
- integration surfaces for enterprise systems and local-first execution.

A visual architecture diagram is useful for orientation, but diagrams should not become the contract source of truth. This note provides a textual decomposition that can accompany diagrams and keep repository ownership boundaries explicit.

## Layer model

### 1. Client, operator, and API surfaces

These surfaces initiate work and inspect outcomes.

Examples:

- operator console;
- CLI/API calls;
- GitHub issue and PR surfaces;
- dashboards for validation, review, and evidence state.

This layer should not own policy decisions. It presents state, receives intent, and exposes evidence.

### 2. Core agentic control plane

This layer owns work lifecycle and orchestration boundaries.

Key responsibilities:

- issue-to-work-order conversion;
- task planning;
- repository snapshot and branch posture;
- sandboxed patch production;
- draft PR creation;
- validation and CI evidence routing;
- review and merge-gate handoff;
- ledger recording.

The control plane must preserve the authority split:

```text
Implementation agent may propose.
Review agent may approve, comment, or request changes.
Policy gate may merge or block.
```

### 3. Security, governance, and policy plane

This layer owns admissibility, hygiene, and merge policy.

Key responsibilities:

- branch admissibility;
- diff hygiene gates;
- denied-path and generated-artifact blocking;
- review-readiness evidence requirements;
- abstract-reasoning verification requirements;
- merge-gate invariants;
- post-merge ledger requirements.

Policy Fabric is the canonical owner for authored policy contracts. AgentPlane consumes policy posture and emits execution evidence.

### 4. Planning and reasoning services

This layer owns typed planning surfaces and verification references.

Key responsibilities:

- planning scope creation;
- plan-node expansion and scoring;
- program candidate induction;
- counterexample search;
- backtracking;
- abstract-rule validation.

TriTRPC owns the typed planning/transport contracts. Semantic artifacts such as program candidates and counterexamples live in semantic-serdes.

### 5. Execution and runner plane

This layer owns execution, evidence emission, and replay surfaces.

Key responsibilities:

- bundle validation;
- placement selection;
- run artifact emission;
- replay artifact emission;
- postcondition artifact emission;
- divergence artifact emission;
- runner cleanup and shell-to-emitter handoff.

AgentPlane owns this runtime boundary. Runners may orchestrate, but Python emitters should own canonical artifact shape.

### 6. Integration adapters

This layer connects external systems without letting them become the policy source of truth.

Examples:

- GitHub;
- CI systems;
- Policy Fabric;
- semantic-serdes;
- TriTRPC;
- HDT / human-digital-twin;
- SourceOS runtime and image-production lanes;
- future weighted relational verifier lanes.

Adapters should pass references and evidence, not shadow authoritative state.

### 7. Capability and worker plane

This layer owns bounded execution capabilities.

Examples:

- local runners;
- tenant worker runtime;
- capability registry;
- sandboxed tool execution;
- future model or verifier workers.

Capabilities must be typed, policy-scoped, and evidence-producing.

## Mapping to current repositories

| Concern | Owning repository |
|---|---|
| Runtime control and execution evidence | `SocioProphet/agentplane` |
| Typed transport and planning service contracts | `SocioProphet/TriTRPC` |
| Semantic verification artifacts | `SocioProphet/semantic-serdes` |
| Abstract reasoning benchmark doctrine | `SocioProphet/socioprophet-standards-storage` |
| Authored policy contracts and gates | `SocioProphet/policy-fabric` |
| First consumer pilot for abstract export repair | `SocioProphet/human-digital-twin` |
| Workspace orchestration and repo-state surface | `SocioProphet/sociosphere` |

## Current v0/v0.5 state

Already established:

- planning-service contracts;
- abstract reasoning benchmark doctrine;
- branch admissibility policy for abstract lanes;
- program candidate and counterexample semantic artifacts;
- validation-time abstract gate in AgentPlane;
- HDT pilot scenario;
- Diff Hygiene Gate policy and validator;
- Agentic PR Work Order contract and validator;
- postcondition/divergence evidence tranche in progress.

Still open:

- runner integration for postcondition/divergence emitters;
- HDT executable benchmark run/report;
- diagram asset linkage;
- weighted relational verifier design.

## Diagram guidance

A visual diagram may accompany this document, but it should be treated as an aid, not as a source of contract truth.

A diagram is acceptable when it:

- preserves repo ownership boundaries;
- labels policy, planning, execution, and integration layers separately;
- distinguishes control-plane authority from capability execution;
- shows evidence and ledger outputs;
- does not imply that a single model owns planning, review, and merge authority.

## Non-goals

This note does not define a production deployment topology.
It does not replace schemas, policy contracts, or runtime validators.
It does not grant autonomous merge authority to any implementation agent.
