# Agent Harness Runtime Contract Map

Status: v0.1 planning baseline  
Owner plane: AgentPlane runtime and evidence  
Consumers: Delivery Excellence, Policy Fabric, Guardrail Fabric, SocioSphere, Memory Mesh, SCOPE-D, SourceOS execution surfaces

## Purpose

Aden/Hive is useful because it packages the production-agent lifecycle as outcome-driven work: describe an outcome, generate a plan, run a graph, observe failures and costs, involve humans, preserve state, and evolve the process. AgentPlane should absorb the runtime contract pattern while keeping our stronger requirements: validation, placement, tamper-evident evidence, deterministic replay, governance context, and promotion control.

This document defines the contract vocabulary AgentPlane should expose so Delivery Excellence can meter agent/human work without becoming a runtime authority.

## Boundary

AgentPlane owns:

- runtime bundle validation
- placement and executor selection
- run/session lifecycle
- event and evidence emission
- replay and promotion artifacts
- reversal/rollback evidence
- runtime linkage to governance context

AgentPlane does not own:

- KPI/OKR definitions or scoreboards; those belong to Delivery Excellence
- policy compilation or grants; those belong to Policy Fabric / Guardrail Fabric
- workspace topology; that belongs to SocioSphere
- long-term memory runtime; that belongs to Memory Mesh
- browser/terminal implementation; those belong to BearBrowser, TurtleTerm, and agent-term
- security exercise execution; that belongs to SCOPE-D

## Required contract family

### OutcomeSpec

The business or platform result to be achieved. It is the input bridge from Delivery Excellence to AgentPlane.

Required semantics:

- outcome id
- success criteria
- hard constraints
- soft preferences
- risk tier
- budget cap
- time cap
- evidence requirements
- customer/stakeholder refs
- linked work items

### PlanGraph

A user-reviewable planning graph before execution. It may include decision branches and explanatory structure that is not directly executable.

Required semantics:

- graph id
- outcome ref
- node summaries
- edges and dependencies
- approval gates
- policy gates
- expected evidence
- unresolved assumptions
- human review status

### GraphSpec

The executable graph compiled from a validated plan graph.

Required node types:

- deterministic task
- LLM loop
- router
- function/tool call
- browser worker
- terminal worker
- connector action
- policy check
- judge/eval
- human approval
- artifact transform
- replay
- promotion gate

Required edge types:

- always
- on success
- on failure
- conditional deterministic
- policy decision
- human decision
- judge decision
- retry/backoff
- abort/escalate

### RunSpec

The concrete execution request.

Required semantics:

- graph ref
- executor constraints
- model profile
- tool grants
- MCP grants
- skill grants
- memory mounts
- filesystem scopes
- network profile
- secret scopes
- cost/time/tool-call limits
- human-in-the-loop policy
- dry-run/live-run mode

### SessionEnvelope

The durable run/session wrapper.

Required semantics:

- session id
- run id
- workspace ref
- graph version
- policy version
- model profile version
- memory snapshot ref
- event stream ref
- checkpoint refs
- human-control event refs
- resume/cancel state

### EvidencePack

The delivery and audit handoff from AgentPlane to downstream consumers.

Required semantics:

- outcome ref
- work item refs
- graph ref
- run/session refs
- validation artifacts
- placement decisions
- run artifacts
- replay artifacts
- event stream refs
- tool/browser/terminal receipts
- policy decision refs
- judge verdict refs
- human-control event refs
- cost summary
- artifact index and hashes
- known gaps

### FailureDiagnosis

The structured explanation of what failed and why.

Required semantics:

- failure id
- failing node/edge/tool/policy ref
- failure type
- observed error
- violated success criteria
- retries attempted
- cost incurred
- evidence refs
- recommended next action

### EvolutionPatch

A proposed change to improve the agent/process. It is never self-promoting.

Allowed targets:

- plan graph
- graph spec
- prompt/runtime instruction
- skill
- MCP/tool grant
- model profile
- memory mount
- policy request
- code patch
- test/eval fixture

Required gates:

- validation
- replay or simulation when available
- policy review
- human approval if risk tier requires it
- rollback/reversal plan

### PromotionGate

The final release/promotion decision for a graph, skill, runtime package, or template.

Required semantics:

- promotion id
- subject ref
- evidence pack ref
- validation result
- replay result
- policy result
- security result
- Delivery Excellence scoreboard impact
- rollback readiness
- decision and actor refs

## Delivery Excellence feed

AgentPlane should expose stable evidence pointers that Delivery Excellence can consume as `DeliveryMetricEvent`, `ScoreboardSnapshot`, `HumanControlEvent`, and `CustomerProofReadout` inputs.

Initial metrics enabled by these contracts:

- validation pass/fail
- placement success/failure
- run success/failure
- replay readiness
- session resume success
- human approval count
- escalation count
- cost by outcome/work item
- tool/browser/terminal failure rate
- promotion readiness
- evidence completeness

## Guardrails

- Logs are not evidence unless referenced from a validated evidence artifact.
- Generated graphs are not executable until validated and policy-gated.
- Evolution patches are not production changes until promoted.
- Human approvals are control events and must be linked to evidence.
- Skill/MCP/tool grants must be explicit and policy-checkable.
- Browser and terminal side effects require scoped receipts.

## Near-term implementation order

1. Add JSON schemas and examples for the contract family.
2. Extend validation to enforce required refs and stable kind/version fields.
3. Emit a minimal `EvidencePack` from an existing example bundle run.
4. Add a Delivery Excellence export path that projects evidence to metric events and scoreboards.
5. Wire SCOPE-D checks into promotion evidence for skill/MCP/browser/terminal risk.
