# Governed Runner Read-Only Tool Surface v0

## Purpose

`tools/governed_runner_tool_surface.py` exposes the governed-runner read-only control surface as a local JSON tool adapter.

It is intended as the safe precursor to a future tool-server / MCP-like surface. It reuses AgentPlane-owned implementation and exposes only operations that are already read-only or evidence-generation only.

## Stable delegate path

The preferred operator path is through the AgentPlane-owned `sp-run` delegate:

```bash
sp-run tool list-tools
sp-run tool call governed_runner.doctor --args-json '{}'
sp-run tool call governed_runner.smoke --args-json '{"output_dir":".socioprophet/smoke/governed-runner"}'
```

Through the Prophet facade:

```bash
prophet governed-runner tool list-tools
prophet governed-runner tool call governed_runner.doctor --args-json '{}'
```

## Direct adapter path

The adapter can also be called directly from a source checkout:

```bash
python3 tools/governed_runner_tool_surface.py list-tools
python3 tools/governed_runner_tool_surface.py call <tool-name> --args-json '<json-object>'
```

## Supported tools

- `governed_runner.doctor`
- `governed_runner.smoke`
- `governed_runner.list`
- `governed_runner.status`
- `governed_runner.inspect`
- `governed_runner.dossier`
- `governed_runner.validate_dossier`
- `governed_runner.preflight`
- `governed_runner.admit`

## Examples

Smoke evidence bundle:

```bash
sp-run tool call governed_runner.smoke \
  --args-json '{"output_dir":".socioprophet/smoke/governed-runner","generated_at":"2026-05-22T12:45:00Z"}'
```

List runs:

```bash
sp-run tool call governed_runner.list \
  --args-json '{"runs_root":".socioprophet/smoke/governed-runner"}'
```

Inspect a run:

```bash
sp-run tool call governed_runner.inspect \
  --args-json '{"run_dir":".socioprophet/smoke/governed-runner/run"}'
```

Preflight projection:

```bash
sp-run tool call governed_runner.preflight \
  --args-json '{"contract_json":"tests/fixtures/runs/governed-run-contract.valid.json","generated_at":"2026-05-22T12:20:00Z"}'
```

Admission receipt construction:

```bash
sp-run tool call governed_runner.admit \
  --args-json '{"contract_json":"tests/fixtures/runs/governed-run-contract.valid.json","preflight_json":"/tmp/preflight.json","authority_state_json":"tests/fixtures/authority/agent-authority-current-state.active.json","projected_cost_usd":0.25}'
```

## Boundary

This tool surface is read-only with respect to governed execution.

It does not:

- execute agents
- run verifier commands
- mutate governed workspace files
- restore rollback state
- update authority
- settle budget

`governed_runner.smoke` writes an evidence bundle only to the requested output directory.

## Error behavior

Unknown tools return `GovernedRunnerToolError` and non-zero exit.

Invalid JSON args return `GovernedRunnerToolError` and non-zero exit.

Missing required arguments return `GovernedRunnerToolError` and non-zero exit.

## Validation

```bash
python3 -m pytest -q tools/tests/test_governed_runner_tool_surface.py
python3 -m pytest -q tools/tests/test_sp_run_tool_adapter.py
```

The tests cover:

- tool listing
- smoke evidence bundle generation
- list/status/inspect
- preflight projection
- admission receipt construction
- unknown tool rejection
- stable `sp-run tool` delegation

## Future surface

A later tool server can wrap this adapter, but it must preserve the same boundary: no execution, no mutation, no restore, no authority update, and no budget settlement unless a separate policy-gated tranche explicitly adds those capabilities.
