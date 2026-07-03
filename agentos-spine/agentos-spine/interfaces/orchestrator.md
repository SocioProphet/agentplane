# OrchestratorAPI (v0.1)

Goal: coordinate multiple roles/agents over one or more repos, while collecting evidence and enforcing gates.

## Required operations

- `spawn(role, config) -> AgentHandle`
- `assign(agent, task) -> TaskHandle`
- `collect(task) -> EvidenceBundle`
- `synthesize(evidence[]) -> Decision`
- `gate(decision, policy) -> GateResult`

## Providers (examples)

- Gastown
- (optional) AIWG ensemble patterns
