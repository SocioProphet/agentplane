# SourceOS Interaction Reference Flow

Status: downstream reference pointer  
Canonical packet: `SourceOS-Linux/sourceos-spec#118`  
Canonical manifest: `examples/interaction-flow/noetica-superconscious-agentplane-agentterm.flow.json`

## AgentPlane role

AgentPlane records the evidence and replay references for the SourceOS interaction substrate.

The canonical reference flow is:

```text
Noetica creates SourceOSInteractionEvent
  -> Superconscious records task-boundary refs
  -> AgentPlane records evidence refs
  -> AgentTerm displays the governance trace
```

## Local references

- Evidence binding doc: `docs/integration/sourceos-interaction-evidence-binding.md`
- Evidence binding schema: `schemas/integration/sourceos-interaction-evidence-binding.v0.1.schema.json`
- Evidence binding check: `python tools/validate_sourceos_interaction_evidence_binding.py`

## Boundary

AgentPlane owns evidence and replay references. The schema remains owned by `SourceOS-Linux/sourceos-spec`; task coordination, display surfaces, policy decisions, identity grants, and memory context remain in their respective planes.
