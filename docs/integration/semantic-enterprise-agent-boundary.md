# Semantic Enterprise Agent Boundary v0.1

AgentPlane consumes `semantic-enterprise-v0.1.0` from `SocioProphet/ontogenesis` as an agent context and admission boundary.

The local fixture is:

- `examples/semantic-enterprise/v0.1/agent-context-boundary.example.json`

The validator is:

- `tools/validate_semantic_enterprise_agent_boundary.py`

## Source release

- Repository: `SocioProphet/ontogenesis`
- Release/tag: `semantic-enterprise-v0.1.0`
- Manifest: `manifests/semantic_enterprise_v0_1_manifest.json`
- Rollup registry: `catalog/semantic_enterprise_v0_1_registry.ttl`
- Named graph fixture: `examples/named-graphs/semantic_sector_named_graphs.ttl`

## Admission model

AgentPlane requires a declared sector context before binding a task to Semantic Enterprise evidence.

The v0.1 fixture covers:

- finance
- threat intelligence
- investigation
- supply chain
- defense/C2

Each sector context preserves:

- scenario path
- query path
- named graph URI fragment
- agent context surface name

## Boundary

Scenario examples are evidence, not instructions. Agent outputs are runtime evidence and do not mutate Ontogenesis source semantics.

The closure model distinguishes:

- `inside_source`: authored Ontogenesis source modules and examples
- `outside_agent_runtime`: AgentPlane task context and evidence binding
- `boundary_membrane`: sector context, source paths, graph references, policy posture, and evidence refs
- `feedback_surface`: AgentPlane outputs as downstream evidence

## Validation

Run:

```bash
make validate
```

or:

```bash
python3 tools/validate_semantic_enterprise_agent_boundary.py
```

## Parent work

- `SocioProphet/agentplane#131`
- `SocioProphet/delivery-excellence#21`
