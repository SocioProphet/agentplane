# sp-run Delegate Surface v0

## Purpose

`sp-run` is the AgentPlane-owned governed-runner delegate command.

This surface exists so higher-level façades such as `prophet-cli` can delegate to AgentPlane without importing AgentPlane logic or reaching into repo-internal implementation paths.

## Boundary

AgentPlane owns:

- governed-runner contracts
- preflight projection
- admission receipt construction
- run dossier generation and validation
- governed-runner smoke evidence generation
- the `sp-run` delegate command

`prophet-cli` should call `sp-run ...` once this delegate is available on `PATH`. It should not duplicate AgentPlane implementation logic.

## Installed command

The package entry point is defined in `pyproject.toml`:

```toml
[project.scripts]
sp-run = "agentplane_cli.sp_run:main"
```

For editable source installs:

```bash
python3 -m pip install -e .
sp-run doctor
```

## Source-checkout wrapper

For local development before packaging/install:

```bash
bash bin/sp-run doctor
bash bin/sp-run preflight tests/fixtures/runs/governed-run-contract.valid.json
bash bin/sp-run smoke --output-dir .socioprophet/smoke/governed-runner
```

The wrapper delegates to:

```bash
python3 tools/sp_run.py ...
```

## Supported commands

```bash
sp-run doctor
sp-run smoke --output-dir .socioprophet/smoke/governed-runner
sp-run preflight <governed-run-contract.json>
sp-run admit <governed-run-contract.json> --preflight <preflight.json> --authority-state <authority-state.json>
sp-run dossier <run_dir>
sp-run validate-dossier <dossier.json>
```

## Non-goals

This delegate does not add execution authority.

It remains read-only and does not:

- execute agents
- run verifier commands
- mutate governed workspace files
- restore rollback state
- update authority
- settle budget

## Validation

```bash
python3 -m pytest -q tools/tests/test_sp_run_delegate_surface.py
```

The tests cover:

- source-checkout wrapper delegation
- Python entry-point delegation
- read-only capability reporting
- smoke evidence bundle generation through both delegate paths

## prophet-cli integration

`prophet-cli` delegates to `sp-run` through its existing façade model:

```bash
prophet agentplane doctor
prophet agentplane preflight <contract.json>
prophet agentplane admit <contract.json> --preflight <preflight.json> --authority-state <authority.json>
prophet agentplane dossier <run_dir>
prophet agentplane validate-dossier <dossier.json>
prophet governed-runner smoke --output-dir .socioprophet/smoke/governed-runner
```

The owning implementation remains here in AgentPlane.
