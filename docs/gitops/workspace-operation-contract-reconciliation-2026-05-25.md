# Workspace Operation Contract Reconciliation — 2026-05-25

Issue: `SocioProphet/agentplane#168`

Source branch audited:

```text
copilot/route-agent-execution-workspace-plane
```

## Finding

The stale branch payload is already present on current `main`:

```text
docs/adr/0008-agent-operation-plane-routing.md
docs/integration/workspace-operation-plane.md
examples/agent-operation-contract.example.json
schemas/agent-operation-contract.schema.v0.1.json
scripts/emit_agent_operation_contract.py
tools/validate_agent_operation_contract.py
tools/tests/test_agent_operation_contract.py
```

The contract-first Workspace Operation Plane routing surface is therefore captured.

## Current replay action

This reconciliation PR adds the missing focused workflow gate:

```text
.github/workflows/agent-operation-contract.yml
```

The workflow validates the schema and example, compiles the emitter and validator, runs the deterministic validator, and runs the focused pytest coverage.

## Boundary

This replay adds validation coverage only.

It does not execute agent operations, mutate workspace artifacts, invoke providers, contact a network, or write external systems.
