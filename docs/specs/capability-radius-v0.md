# Capability Radius v0

## Purpose

Defines the six capability radius levels (R0–R5) that bound what an agent, tool, or service can do within the tensegrity runtime. Radius is a tension member: it scopes tool grants, CGRM decisions, and revocation paths.

## Radius Levels

| Level | Name                   | Scope                                                                                   | Tension Members Required                    |
|-------|------------------------|-----------------------------------------------------------------------------------------|---------------------------------------------|
| R0    | observe-local          | Read from in-process or local context; no side effects outside the execution envelope   | policy, identity                            |
| R1    | query-bounded          | Query services or data stores with read-only scope; results stay in-process             | policy, identity, provenance                |
| R2    | transform-scoped       | Produce or modify artifacts within a governed workspace; no direct writes to shared state | policy, identity, provenance, evidence, replay |
| R3    | write-governed         | Write to governed repositories, ledgers, or evidence stores; requires signed receipt    | policy, identity, provenance, evidence, replay, revocation |
| R4    | deploy-staged          | Deploy to staged or sandboxed environments; Signadot or equivalent runtime gate required | policy, identity, provenance, evidence, replay, revocation, audit |
| R5    | deployment-host-mutation | Mutate production hosts, release branches, or live infrastructure; requires explicit admission gate and senior authority ref | policy, identity, provenance, evidence, replay, revocation, audit, post_authority_ref |

## Radius and Tool Grants

A tool grant may not exceed the actor's declared capability radius. Attempting to invoke a tool with a radius higher than the actor's current grant level causes the dispatch to transition to `blocked` with a RationalGRL defeater.

## Radius and Oversteer

Rapid radius escalation (R0 → R3 in a single session without intermediate evidence) is an oversteer indicator. See `cybernetic-oversteer-v0.md`.

## Radius Profile

The live capability radius profile for an actor or service is declared in `examples/reachability/agent-capability-radius.example.json`.
