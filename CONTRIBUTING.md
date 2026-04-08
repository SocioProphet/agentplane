# Contributing to agentplane

Thank you for your interest in contributing.  
This guide covers the local development setup, coding conventions, and the PR workflow.

---

## Before you start

- All contributions must be compatible with the **MIT license**.
- **No AGPL dependencies** may be introduced into this repository. See [ADR-0001](docs/adr/0001-no-agpl-dependencies.md). The bundle validator hard-enforces this at runtime; the same constraint applies to tooling added here.
- Open-source only. No proprietary runtimes, SDKs, or libraries.

---

## Prerequisites

| Tool | Purpose | Minimum version |
|---|---|---|
| Nix | VM builds | 2.18 |
| Python 3 | Scripts and tests | 3.9 |
| Lima + `lima-nixbuilder` | Default local executor | latest |
| `rsync` | Artifact syncing | any |
| `ssh` | Executor probes | any |
| `gh` CLI | Opening PRs | any |

---

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/SocioProphet/agentplane
cd agentplane

# 2. Verify Nix builders
scripts/doctor.sh

# 3. Verify executor reachability
scripts/doctor-executor.sh

# 4. Run syntax checks
scripts/hygiene.sh

# 5. Run the full demo to confirm everything works end-to-end
scripts/demo.sh
```

---

## Lint and test

CI runs the following checks on every push and PR (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)):

```bash
# Bash syntax check
bash -n runners/qemu-local.sh

# Python syntax check (all scripts/*.py)
python3 -m py_compile scripts/*.py

# Bundle validation (validates example bundle + emits ValidationArtifact)
python3 scripts/validate_bundle.py bundles/example-agent/bundle.json
```

Run these locally before pushing:

```bash
scripts/hygiene.sh
python3 scripts/validate_bundle.py bundles/example-agent/bundle.json
```

### Receipt smoke test

```bash
python tools/receipt_smoke_test.py examples/receipts/gakw_hybrid_warm_trace.example.json
```

This assembles a receipt from the example trace and verifies energy consistency. Run it whenever you modify `examples/receipts/` or `tools/`.

---

## Making changes

### Adding or modifying a bundle

1. Create a new directory under `bundles/` with `bundle.json`, `vm.nix`, and `smoke.sh`.
2. Validate it: `python3 scripts/validate_bundle.py bundles/<your-bundle>/bundle.json`
3. Ensure `metadata.licensePolicy.allowAGPL` is `false`.
4. Ensure `metadata.source.git.rev` is set to a real commit SHA (not `"UNSET"`) before merging.
5. Run a demo: `scripts/demo.sh bundles/<your-bundle>`

### Modifying schemas

- Schemas live in `schemas/`. See [schemas/README.md](schemas/README.md).
- **Do not make breaking changes to existing versioned schemas** (e.g., `bundle.schema.v0.1.json`). Instead, create a new version file (e.g., `bundle.schema.v0.2.json`) and update the validator.
- `bundle.schema.patch.json` is a staged patch fragment for future agent-runtime fields. It is not yet enforced by the validator; document any additions there in [schemas/README.md](schemas/README.md).

### Modifying the runner

- `runners/qemu-local.sh` implements the backend-agnostic contract defined in `runners/runner.md`.
- Always run `bash -n runners/qemu-local.sh` after edits.
- The runner must remain idempotent for `smoke`, `promote`, `rollback`, and `status` commands.

### Adding a new executor

1. Add an entry to `fleet/inventory.json`.
2. Run `scripts/doctor-executor.sh` to verify reachability and capabilities.
3. Document the executor's `kvm` capability accurately — it affects backend selection.

### Adding documentation

- Place conceptual/architectural docs in `docs/`.
- Place integration guides in `docs/integration/`.
- Record significant design decisions as ADRs in `docs/adr/`. See [docs/adr/README.md](docs/adr/README.md).
- Update [docs/README.md](docs/README.md) when adding a new file to `docs/`.
- Update the table in [README.md](README.md) when adding a top-level doc.

---

## Pull request workflow

```bash
# Create a branch, commit staged changes, push, and open a PR in one step:
scripts/pr.sh <branch-name> "<commit message>" [paths...]

# Example — stage specific files only:
scripts/pr.sh feat/new-executor "feat: add x86_64 fleet executor" fleet/inventory.json

# Example — stage all tracked changes:
scripts/pr.sh docs/fix-adr "docs: add ADR-0008"
```

> **Note:** `scripts/pr.sh` guards against nested `.git` directories (submodule accidents) and
> runs `scripts/hygiene.sh` before committing. If hygiene fails, the PR will not be opened.

PRs target the `main` branch. All checks in CI must pass before merging.

---

## Code style

- **Python:** Standard library only (no third-party packages) unless explicitly justified and approved. Follow PEP 8. Use `from __future__ import annotations` for forward references.
- **Bash:** `set -euo pipefail` at the top of every script. Use `command -v` to check for tool availability. Disable pagers (`git --no-pager`, etc.) in scripts.
- **JSON schemas:** Draft 2020-12. Keep `"required"` arrays sorted. Add `"description"` to non-obvious properties.
- **Comments:** Only where the code's intent is genuinely non-obvious. Match the surrounding style.

---

## Architecture decisions

Before making a significant design change, check [docs/adr/README.md](docs/adr/README.md) to see if it has already been decided. If your change reverses or supersedes an existing ADR, update the old ADR's status and write a new one.

---

## CODEOWNERS

All files are owned by `@michaelheller` (see [`.github/CODEOWNERS`](.github/CODEOWNERS)). Tag the owner in your PR for review.
