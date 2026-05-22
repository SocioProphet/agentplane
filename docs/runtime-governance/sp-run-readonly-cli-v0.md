# sp-run Read-Only CLI v0

## Purpose

`sp-run` is the first operator-facing CLI surface for the governed runner lane.

This v0 surface is intentionally read-only. It exposes the evidence product without adding execution authority:

- check local governed-run evidence tooling
- build a `RunDossier` from a governed run folder
- validate a `RunDossier` JSON file

It does not run agents, execute verifier commands, mutate files, restore rollback state, or change authority.

## Commands

### `doctor`

```bash
python3 tools/sp_run.py doctor
```

Checks that the local repository has the required read-only governed-run evidence files:

- GovernedRunContract schema
- RunDossier schema
- AttemptAdmissionReceipt schema
- RollbackBoundary schema
- RollbackResult schema
- RunDossier builder
- RunDossier validator

The command returns JSON with:

- `tool`
- `mode`
- `ok`
- `repo_root`
- `capabilities`
- `non_goals`
- file existence records

### `dossier`

```bash
python3 tools/sp_run.py dossier <run_dir>
```

Builds a `RunDossier` from a governed run evidence folder.

Optional deterministic timestamp:

```bash
python3 tools/sp_run.py dossier <run_dir> --generated-at 2026-05-22T12:10:00Z
```

Optional output file:

```bash
python3 tools/sp_run.py dossier <run_dir> --output run-dossier.json
```

### `validate-dossier`

```bash
python3 tools/sp_run.py validate-dossier <dossier.json>
```

Validates a dossier against the `RunDossier` schema and semantic checks.

## Boundary

This CLI is read-only by design.

Non-goals for v0:

- no agent execution
- no verifier execution
- no file mutation
- no rollback restoration
- no authority updates
- no budget settlement
- no MCP server

## Validation

```bash
python3 -m pytest -q tools/tests/test_sp_run_cli.py
```

The tests cover:

- `doctor` reports read-only capabilities
- `dossier` builds a ready dossier from synthetic receipts
- `validate-dossier` accepts a valid fixture
- `validate-dossier` rejects a missing file

## Roadmap

Later CLI expansion should add commands only after the corresponding evidence and policy gates are present:

- `preflight`
- `admit`
- `status`
- `list`
- `inspect`

Any future `run` command must remain policy-gated by `GovernedRunContract`, safety preflight, Agent Registry authority state, TrustOps runtime action mapping, budget admission, and rollback readiness.
