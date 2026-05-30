# SourceOSInteractionEvent evidence binding

## Status

Fixture, schema, and validation binding only. This document does not add runtime execution behavior.

AgentPlane owns execution evidence, replay artifacts, validation artifacts, placement artifacts, and run artifacts. It may attach those authoritative references to a `SourceOSInteractionEvent` governance trace so Noetica, AgentTerm, and Superconscious can render the same interaction lifecycle without owning execution evidence semantics.

## Canonical interaction contract

`SourceOSInteractionEvent` is owned by `SourceOS-Linux/sourceos-spec`:

- `schemas/SourceOSInteractionEvent.json`
- `generated/typescript/sourceos-interaction-event.ts`
- `generated/python/sourceos_interaction_event.py`

AgentPlane does not own this schema. AgentPlane owns the evidence artifacts referenced by the interaction event.

## Required AgentPlane references

A SourceOS interaction evidence binding records:

- `source_interaction_event_ref`
- `result_interaction_event_ref`
- `agentplane_run_ref`
- `validation_artifact_ref`
- `placement_decision_ref`
- `run_artifact_ref`
- `evidence_artifact_refs`
- `replay_ref`
- `context_pack_refs`
- `policy_decision_refs`
- `redaction_refs`

The binding exists so an interaction event can carry AgentPlane evidence references without copying raw execution logs, unrestricted stdout/stderr, secrets, credentials, or private chain-of-thought.

## Authority boundaries

AgentPlane owns:

- execution evidence;
- run artifacts;
- replay artifacts;
- validation artifacts;
- placement artifacts;
- evidence bundle refs.

AgentPlane does not own:

- browser, terminal, Matrix, or Noetica UI surfaces;
- Policy Fabric policy admission;
- Agent Registry identity, grants, sessions, or revocation;
- Memory Mesh durable memory or context-pack semantics;
- SourceOSInteractionEvent schema ownership.

## Expected flow

```text
Noetica / AgentTerm / Superconscious source event
  -> SourceOSInteractionEvent ref
  -> AgentPlane validation / placement / run / evidence / replay
  -> SourceOS interaction evidence binding
  -> result SourceOSInteractionEvent ref with AgentPlane refs attached
  -> AgentTerm or Noetica renders the governance trace
```

## Payload posture

The binding is reference-oriented. It must not contain raw execution logs, unrestricted shell output, unrestricted transcripts, credentials, secrets, private chain-of-thought, or unredacted stdout/stderr.

Use artifact refs and hashes instead.

## Validation

Run:

```bash
python3 tools/validate_sourceos_interaction_evidence_binding.py tests/fixtures/integration/sourceos-interaction-evidence-binding.valid.json
```

Invalid fixtures prove that missing replay refs and raw log leakage fail closed.
