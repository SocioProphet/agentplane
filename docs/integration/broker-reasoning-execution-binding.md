# Broker Reasoning Execution Binding

## Purpose

AgentPlane is the governed execution and replay plane for the cross-cloud services broker model.

It does not own broker doctrine or policy authorship. It validates, places, runs, and replays broker-related execution bundles and emits evidence artifacts.

## AgentPlane responsibilities

AgentPlane should execute:

- provider-binding validation bundles
- service-offering smoke tests
- blueprint fulfillment tests
- provider adapter conformance tests
- exit-plan simulations
- continuity tests
- cost-meter validation jobs
- policy-decision replay jobs
- evidence completeness checks

## Inputs

AgentPlane broker execution inputs include:

- validated broker bundle
- provider binding
- policy decision or exception record
- execution placement constraints
- smoke/continuity/exit test definitions

## Outputs

AgentPlane should emit:

- `ValidationArtifact`
- `PlacementDecision`
- `RunArtifact`
- `ReplayArtifact`
- promotion or reversal evidence where applicable

## Broker rule

BrokerPlane coordinates lifecycle. PolicyPlane decides. AgentPlane executes and emits replayable evidence.

## Design invariant

AgentPlane must not invent policy authority. It executes only after policy and broker context are supplied.
