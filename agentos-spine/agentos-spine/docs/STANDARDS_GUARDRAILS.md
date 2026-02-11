# Standards and architecture guardrails

These guardrails exist to prevent accidental architectural drift while integrating many repos/tools.

## 1) SourceOS independence

SourceOS must operate without socios.
Socios is **opt-in** and gated (Proof-of-Life + signed intent).

## 2) Protocol directionality

If we use sociosphere as workspace/orchestrator and TritRPC as protocol:
- sociosphere -> tritrpc is allowed
- tritrpc -> sociosphere is forbidden

This prevents circular dependencies between the orchestrator and the protocol spec.

## 3) Canonical truth

- Canonical standards live in the SocioProphet standards repos (+ TriTRPC spec/fixtures).
- Canonical project truth is git + AIWG artifacts.
- Memory providers (Mem0/Fortemi/etc.) are caches/services and must be exportable.

## 4) Boxing rule

Anything not permissively licensed (MIT/Apache/BSD/CC0) is boxed behind:
- an adapter interface, and
- a runtime boundary (separate process/container/VM).

This keeps replacements cheap.
