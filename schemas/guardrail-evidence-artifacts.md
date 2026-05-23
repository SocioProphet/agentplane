# Guardrail Evidence Artifact Schemas

Status: informative schema companion note.

This note preserves the guardrail evidence documentation from the stale guardrail evidence artifact branch without replacing the current `schemas/README.md`, which now contains newer schema families that the stale branch did not know about.

## Schemas

| File | Kind | Version | Description |
|---|---|---|---|
| `policy-decision-artifact.schema.v0.1.json` | `PolicyDecisionArtifact` | v0.1 | AgentPlane evidence wrapper for SourceOS guardrail-fabric policy decisions. |
| `stop-gate-artifact.schema.v0.1.json` | `StopGateArtifact` | v0.1 | Evidence record for agent completion gates, false-done prevention, and human override posture. |

## PolicyDecisionArtifact

`PolicyDecisionArtifact` wraps a `sourceos.guardrail.decision.v0.1` decision emitted by `SocioProphet/guardrail-fabric` so AgentPlane can treat policy decisions as first-class evidence.

It records:

- AgentPlane session and task references;
- guardrail source system, adapter, version, repository, and commit;
- embedded SourceOS policy decision artifact;
- AgentPlane result interpretation: `allow`, `blocked`, `needs_human`, `redacted`, `quarantined`, or `deferred`;
- decision log, tool event, redaction, and human override references;
- optional governance context.

AgentPlane should not reimplement guardrail policy logic. It should ingest and preserve the decision, then use the interpreted result for stop gates and runtime transitions.

## StopGateArtifact

`StopGateArtifact` records the evidence behind an agent completion gate. Stop gates prevent false-done completion by requiring branch, commit, push, PR, CI, policy, summary, and human-review evidence where applicable.

It records:

- session and task references;
- gate identity and policy reference;
- final result: `pass`, `fail`, `needs_human`, `waived`, or `not_applicable`;
- per-check result, reason, remediation, evidence references, and related policy decision references;
- optional human override or break-glass override reference, depending on the active schema version;
- related policy decision, run, replay, pull request, CI, and summary artifact references.

A stop gate that fails should produce actionable remediation rather than a generic blocked state.

## Validation

The structural validator is:

```bash
python3 tools/validate_guardrail_evidence_artifacts.py
```

The validator intentionally uses only the Python standard library so the normal `make validate` path does not gain an additional dependency.

## Current mainline posture

Current `main` preserves the stale branch guardrail evidence schemas and validator. It additionally extends `StopGateArtifact` with break-glass override references, so the stale branch must remain do-not-merge.
