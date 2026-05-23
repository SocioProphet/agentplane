# Branch Audit Known Findings — 2026-05-23

Issue: `SocioProphet/agentplane#168`

## Purpose

This manifest records the first durable audit pass over the known active branches listed in `agentplane#168`.

It does not close or discard any branch. It records compare state against current `main`, changed-file inventory, content category, and recommended disposition.

Current main at audit time:

```text
55504f17ceedc75da86976556cfb26d3e114bf2e
```

## Findings

| Branch | Compare state | Ahead / behind | Changed files | Category | Disposition |
|---|---:|---:|---|---|---|
| `feature/shir-governed-chain-job-fixture-v0.1b` | diverged | +4 / -95 | `.github/workflows/validate-shir-governed-chain-job.yml`; `tools/README.md`; `tools/shir_governed_chain_job.py` | `unique-workflow-ci`, `unique-runtime-code` | Replay first only after focused review; avoid direct stale merge. |
| `work/event-capability-admission-refresh` | diverged | +3 / -95 | `docs/integration/event-capability-admission.md`; `examples/orchestration/event-capability.records.json`; `scripts/validate_event_capability_admission.py` | `unique-contract-schema-fixture` | Replay after SHIR. Payload is docs/example/validator and likely low-risk. |
| `copilot/add-action-proposal-admission-receipt-contract` | diverged | +2 / -94 | `docs/integration/action-contracts.md`; `fixtures/action-contracts/*`; `schemas/action-*.json`; `schemas/runtime-receipt.schema.v0.1.json`; `tools/validate_action_contracts.py`; README/Makefile indexes | `unique-contract-schema-fixture` | Replay as current-main contract tranche. Avoid stale Makefile rewrite. |
| `copilot/route-agent-execution-workspace-plane` | diverged | +2 / -99 | `docs/adr/0008-agent-operation-plane-routing.md`; `docs/integration/workspace-operation-plane.md`; `examples/agent-operation-contract.example.json`; `schemas/agent-operation-contract.schema.v0.1.json`; `scripts/emit_agent_operation_contract.py`; `tools/validate_agent_operation_contract.py`; tests and indexes | `unique-contract-schema-fixture`, `unique-runtime-code` | Replay after action-contracts; inspect executable script before merge. |
| `codex/run-replay-artifacts-v0-1` | diverged | +6 / -170 | `docs/sociosphere-bridge.md`; `schemas/replay-artifact.schema.v0.1.json`; `schemas/run-artifact.schema.v0.1.json`; `scripts/emit_replay_artifact.py`; `scripts/emit_run_artifact.py` | `unique-contract-schema-fixture`, `unique-runtime-code` | Replay before larger integration bundles because run/replay primitives are foundational. |
| `banking-twin/agentplane-execution-bundles-v0-1` | diverged | +17 / -147 | `bundles/*/bundle.json`; `bundles/*/smoke.sh`; `bundles/*/vm.nix`; `docs/banking-execution-bundles.md` | `needs-human-claim-review`, `unique-runtime-code` | Hold for later review. Contains domain-specific execution bundles and shell smoke files. |
| `agentplane-runtime-enforcement-code` | diverged | +1 / -151 | `scripts/evaluate_control_matrix_gate.py`; `scripts/validate_bundle.py` | `unique-runtime-code` | Hold until contract surfaces are consolidated. Higher risk because it modifies enforcement scripts. |

## Recommended merge order from this pass

1. Replay `work/event-capability-admission-refresh` first if we want a low-risk contract/doc/validator tranche.
2. Replay `codex/run-replay-artifacts-v0-1` next if run/replay primitives are needed for downstream integration.
3. Replay `copilot/add-action-proposal-admission-receipt-contract` after checking overlap with current action-contract validation.
4. Replay `copilot/route-agent-execution-workspace-plane` after action contracts because it introduces a larger operation-plane surface.
5. Review `feature/shir-governed-chain-job-fixture-v0.1b` before replay because it includes a runtime helper and workflow.
6. Hold `banking-twin/agentplane-execution-bundles-v0-1` for claim/domain review.
7. Hold `agentplane-runtime-enforcement-code` for focused runtime-enforcement review.

## Rules carried forward

- Do not directly merge stale branches.
- Replay accepted payloads onto current `main`.
- Avoid wholesale Makefile rewrites unless unavoidable.
- Prefer focused validators and workflows for isolated surfaces.
- Close stale branches/PRs only after replacement PRs land or content is proven present on `main`.
