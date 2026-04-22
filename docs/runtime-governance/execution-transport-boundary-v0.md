# Execution transport boundary v0

This note records the current transport split for execution-related work.

## Local subprocess execution

For local runner↔adapter subprocess execution, the canonical contract surface is:
- `SociOS-Linux/workstation-contracts`
- M2 IPC v1.0 (NDJSON over stdio)

This is the correct seam for local plugin-style execution where:
- the runner spawns adapters directly
- line-delimited JSON remains useful for debugging and low-friction implementation
- transport determinism is less important than stable local process semantics

## Remote canonical execution

For remote/cross-host/cross-service execution and authenticated transport, the canonical authority is:
- `SocioProphet/TriTRPC`

This is the correct seam for:
- deterministic byte fixtures
- authenticated transport requirements
- cross-language canonicalization and parity
- standards-grade remote transport

## Role of agentplane

`agentplane` should be able to reference both transport families without redefining either.

The execution-plane object model should therefore carry:
- local execution protocol refs where local adapter execution is used
- remote execution protocol refs where deterministic remote transport is used

The higher-level build/release/evidence objects live above the transport layer and should remain reusable across both.
