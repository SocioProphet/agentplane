# Governed Runner v0.1 Read-Only Release Dossier

Status: v0.1 read-only release surface

Owning repo: `SocioProphet/agentplane`

## Purpose

This dossier is the canonical release/readiness record for the governed-runner v0.1 read-only surface.

It consolidates the implemented contracts, receipts, CLI commands, product facade, install path, validation gates, and hard boundaries for the governed-runner lane.

The release is intentionally read-only with respect to governed execution. It proves that contracts, safety posture, authority posture, admission receipts, evidence folders, run dossiers, inspection, and local tool adapters compose without granting live execution authority.

## Cross-repo ownership map

| Plane | Repo | Responsibility |
|---|---|---|
| Safety posture | `SocioProphet/guardrail-fabric` | TrustOps gate semantics, safety preflight, runtime action mapping |
| Authority posture | `SocioProphet/agent-registry` | agent authority decisions, current authority state, restoration decisions |
| Governed-runner evidence | `SocioProphet/agentplane` | run contracts, preflight projection, attempt admission receipts, rollback evidence, dossiers, smoke, inspection, local tool adapter, `sp-run` |
| Product facade | `SocioProphet/prophet-cli` | stable `prophet governed-runner ...` facade delegating to `sp-run` |
| Install path | `SocioProphet/homebrew-prophet` | Homebrew formulae for `prophet-cli` and `agentplane` |

## Release surface

The AgentPlane-owned command is `sp-run`.

Supported read-only commands:

```bash
sp-run doctor
sp-run smoke --output-dir ./.socioprophet/smoke/governed-runner
sp-run list --runs-root ./.socioprophet/smoke/governed-runner
sp-run status ./.socioprophet/smoke/governed-runner/run
sp-run inspect ./.socioprophet/smoke/governed-runner/run
sp-run preflight ./governed-run-contract.json
sp-run admit ./governed-run-contract.json --preflight ./preflight-receipt.json --authority-state ./agent-authority-current-state.json --projected-cost-usd 0.25
sp-run dossier ./.socioprophet/smoke/governed-runner/run
sp-run validate-dossier ./run-dossier.json
sp-run tool list-tools
sp-run tool call governed_runner.doctor --args-json '{}'
```

The Prophet facade delegates to `sp-run`:

```bash
prophet governed-runner doctor
prophet governed-runner smoke --output-dir ./.socioprophet/smoke/governed-runner
prophet governed-runner list --runs-root ./.socioprophet/smoke/governed-runner
prophet governed-runner status ./.socioprophet/smoke/governed-runner/run
prophet governed-runner inspect ./.socioprophet/smoke/governed-runner/run
prophet governed-runner tool list-tools
```

## Install path

Development install through Homebrew:

```bash
brew tap SocioProphet/prophet
brew install prophet-cli agentplane
```

Direct source-checkout path:

```bash
python3 -m pip install -e .
sp-run doctor
```

Source wrapper path:

```bash
bash bin/sp-run doctor
```

The v0 `sp-run` package entry point delegates to `tools/sp_run.py` in an AgentPlane source or editable checkout. If that delegate is unavailable, `sp-run` returns `127` and emits a structured `SpRunInstallError` diagnostic.

## Core artifacts

### Run contract

`GovernedRunContract` is the canonical input contract for a governed run attempt.

It binds:

- run id;
- objective;
- workspace reference;
- agent reference;
- authority grant reference;
- policy bundle reference;
- TrustOps gate policy reference;
- budget;
- verification plan;
- allowed and denied paths;
- network posture;
- execution profile;
- mutation mode;
- rollback requirement;
- receipt requirements.

### Preflight receipt

`PreflightReceipt` records a read-only AgentPlane projection from `GovernedRunContract` into safety posture.

It explicitly records:

```json
"authoritative_safety_owner": "SocioProphet/guardrail-fabric"
```

The receipt may produce:

- `pass`
- `require-review`
- `block`

### Authority current state

`AgentAuthorityCurrentState` is owned by `SocioProphet/agent-registry` and consumed by AgentPlane admission.

Authority state must derive from explicit authority decisions or restoration decisions. Raw TrustOps receipts are evidence, not authority mutation.

### Attempt admission receipt

`AttemptAdmissionReceipt` is produced from:

- `GovernedRunContract`
- `PreflightReceipt`
- Agent Registry `AgentAuthorityCurrentState`

It answers whether one attempt may be admitted. It does not execute the attempt.

### Rollback evidence

`RollbackBoundary` and `RollbackResult` record rollback-related evidence.

v0.1 does not perform rollback restoration. It records and validates evidence only.

### Run dossier

`RunDossier` is the operator-facing summary derived from receipts only.

It summarizes:

- run id;
- attempt count;
- overall status;
- latest admission;
- latest rollback;
- budget summary;
- receipt refs;
- missing receipts;
- recommended next action.

A `ready` dossier cannot hide missing receipts.

## Smoke path

The deterministic smoke path proves the read-only composition:

```text
GovernedRunContract
  -> PreflightReceipt
  -> AttemptAdmissionReceipt
  -> evidence folder
  -> RunDossier
  -> smoke summary
```

Command:

```bash
sp-run smoke --output-dir ./.socioprophet/smoke/governed-runner
```

Expected evidence folder:

```text
<output-dir>/
  run/
    governed-run-contract.json
    attempts/
      001/
        preflight-receipt.json
        attempt-admission-receipt.json
        runtime-attempt-receipt.json
        verification-result.json
        rollback-boundary.json
        rollback-result.json
  run-dossier.json
  smoke-result.json
```

## Local JSON tool adapter

The read-only local tool adapter is exposed through:

```bash
sp-run tool list-tools
sp-run tool call governed_runner.doctor --args-json '{}'
```

Supported tools:

- `governed_runner.doctor`
- `governed_runner.smoke`
- `governed_runner.list`
- `governed_runner.status`
- `governed_runner.inspect`
- `governed_runner.dossier`
- `governed_runner.validate_dossier`
- `governed_runner.preflight`
- `governed_runner.admit`

The tool adapter is a local JSON adapter only. It is the safe precursor to a future tool-server surface.

## Validation gates

Focused workflow:

```text
.github/workflows/governed-runner-readonly.yml
```

Repo-level Makefile targets:

```bash
make validate-governed-run-contract
make validate-preflight-receipt
make validate-attempt-admission-receipt
make validate-rollback-receipts
make validate-run-dossier
make validate-governed-runner-readonly
make validate
```

Focused test suites:

```bash
python3 -m pytest -q tools/tests/test_sp_run_cli.py
python3 -m pytest -q tools/tests/test_sp_run_preflight_cli.py
python3 -m pytest -q tools/tests/test_sp_run_admit_cli.py
python3 -m pytest -q tools/tests/test_sp_run_delegate_surface.py
python3 -m pytest -q tools/tests/test_sp_run_install_mode.py
python3 -m pytest -q tools/tests/test_governed_runner_smoke.py
python3 -m pytest -q tools/tests/test_sp_run_run_store_inspection.py
python3 -m pytest -q tools/tests/test_governed_runner_tool_surface.py
python3 -m pytest -q tools/tests/test_sp_run_tool_adapter.py
```

## Hard non-goals for v0.1

The v0.1 release does not add or authorize:

- live agent execution;
- verifier execution;
- governed workspace mutation;
- rollback restoration;
- authority mutation;
- budget settlement;
- provider invocation;
- network activity on behalf of a run;
- background daemon behavior;
- durable workspace graph storage;
- durable memory writeback;
- policy adjudication outside the owning policy planes.

Any future tranche that adds one of these capabilities must be separately policy-gated and must introduce new receipts, negative fixtures, and validation boundaries before runtime behavior is enabled.

## Release readiness claim

The governed-runner v0.1 surface is ready as a read-only evidence and operator-inspection layer.

It is not a live execution engine.

It is safe to expose through `sp-run` and `prophet governed-runner ...` because the implemented commands are read-only, receipt-derived, or evidence-bundle generation only.

## Next gated phase

The next phase should be issue-driven before implementation.

Required design issues:

1. policy-gated verifier execution;
2. policy-gated rollback restore;
3. budget settlement receipt;
4. authority-state lookup/resolution command;
5. Guardrail Fabric preflight handoff contract;
6. AgentPlane stable release formula generation procedure.

No runtime mutation should be implemented until these design issues have explicit acceptance criteria, negative fixtures, and cross-plane ownership boundaries.
