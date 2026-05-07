# OpsHistory AgentPlane Contract

Status: initial contract-capture specification.

AgentPlane consumes bounded OpsHistory context-pack references and emits evidence references back into the OpsHistory fabric.

AgentPlane remains the authority for validation, placement, run, replay, and evidence artifacts. OpsHistory references those artifacts; it does not replace them.

## Intake posture

AgentPlane intake is reference-oriented:

- context-pack references;
- source event references;
- policy decision references;
- agent registry grant references;
- artifact references;
- redaction references;
- workroom, topic, and session scope.

AgentPlane must not infer execution context by reading operator conversations, browser state, or operational receipt material. Context must arrive through explicit context-pack references.

## Emission posture

AgentPlane may emit OpsHistory event references for validation, placement, run, replay, evidence artifact emission, policy denial, redaction invalidation, and handoff.

## Non-goals

- No live OpsHistory service implementation.
- No Memory Mesh runtime ingestion.
- No browser export implementation.
- No operational receipt export implementation.
- No execution behavior changes.
