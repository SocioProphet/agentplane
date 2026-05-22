# Workroom Context Evidence

Status: v0.1 evidence bridge

## Purpose

This note defines AgentPlane's first evidence-only bridge to Prophet Workspace Context Fabric.

AgentPlane does not own Workroom, ProfessionalWorkroom, ContextGraph, provider capture, provider projection, share grant, or recall candidate semantics. Those are workspace-domain objects. AgentPlane records execution-side evidence that a governed run was associated with those refs.

## Boundary

AgentPlane owns:

- bundle validation;
- placement decisions;
- run artifacts;
- replay artifacts;
- evidence records for governed execution.

AgentPlane does not own:

- workspace product semantics;
- durable recall/writeback;
- agent identity or grants;
- platform event storage;
- policy decision semantics.

## Evidence surface

The v0.1 surface is `WorkroomContextEvidence`.

It captures refs to:

- base Workroom;
- optional ProfessionalWorkroom profile;
- ContextGraph;
- WorkspaceContextRuntimeBinding;
- Agent Registry refs;
- Memory Mesh context pack or promotion refs;
- Prophet Platform evidence refs;
- AgentPlane bundle/run/replay refs.

## Non-goals

This tranche does not add runtime execution behavior, provider calls, durable recall writeback, policy adjudication, or platform storage. It only adds a validated evidence packet shape and example.
