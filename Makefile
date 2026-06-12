.PHONY: validate test validate-agent-cycle-health validate-authority-dependency-evidence validate-prometheus-sr validate-reasoning-failure-traces validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-semantic-enterprise-agent-boundary validate-ops-history-contracts validate-action-contracts validate-agent-operation-contract validate-superconscious-reasoning-import validate-agent-harness-runtime-contracts validate-bounded-action-loop agentplane-evidence-receipt-composition-tier2-binding-ci lawful-learning-phase9-contract-ci validate-evidence-receipt-binding validate-semantic-activation-receipt validate-governed-run-contract validate-preflight-receipt validate-attempt-admission-receipt validate-verification-execution-receipt validate-synthetic-verification-receipt validate-governed-runner-v0-2-contract-chain validate-budget-settlement-receipt validate-rollback-receipts validate-run-dossier validate-governed-runner-readonly validate-workroom-context-evidence validate-wallguard-collaboration-admission validate-prophet-mesh-agentplane-adapter validate-civic-stack-runtime-evidence validate-conversational-evidence validate-concept-to-artifact-lineage validate-model-routing-lane-receipts validate-shir-governed-chain-job validate-device-actuation-boundary validate-reasoning-run-evidence validate-graph-aware-work-orders validate-orggov-work-order-evidence-bridge validate-substrate-trust-gates validate-workcell-stop-gates validate-rollback-restore validate-agentic-runtime-state validate-wallguard-collaboration-gate

validate: validate-agent-cycle-health validate-authority-dependency-evidence validate-prometheus-sr validate-reasoning-failure-traces validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-semantic-enterprise-agent-boundary validate-ops-history-contracts validate-action-contracts validate-agent-operation-contract validate-superconscious-reasoning-import validate-agent-harness-runtime-contracts validate-bounded-action-loop agentplane-evidence-receipt-composition-tier2-binding-ci lawful-learning-phase9-contract-ci validate-evidence-receipt-binding validate-semantic-activation-receipt validate-governed-run-contract validate-preflight-receipt validate-attempt-admission-receipt validate-verification-execution-receipt validate-synthetic-verification-receipt validate-governed-runner-v0-2-contract-chain validate-budget-settlement-receipt validate-rollback-receipts validate-run-dossier validate-governed-runner-readonly validate-workroom-context-evidence validate-wallguard-collaboration-admission validate-prophet-mesh-agentplane-adapter validate-civic-stack-runtime-evidence validate-conversational-evidence validate-concept-to-artifact-lineage validate-model-routing-lane-receipts validate-shir-governed-chain-job validate-device-actuation-boundary validate-reasoning-run-evidence validate-graph-aware-work-orders validate-orggov-work-order-evidence-bridge validate-substrate-trust-gates validate-workcell-stop-gates validate-rollback-restore validate-agentic-runtime-state validate-wallguard-collaboration-gate
	python3 tools/validate_execution_timing.py

validate-governance-context:
	python3 scripts/verify_governance_context.py

validate-lattice-data-governai-execution-refs:
	python3 tools/validate_lattice_data_governai_execution_refs.py

validate-lattice-runtime-profile-refs:
	python3 tools/validate_lattice_runtime_profile_refs.py

validate-network-native-assistant-evidence:
	python3 tools/validate_network_native_assistant_evidence.py

validate-guardrail-evidence-artifacts:
	python3 tools/validate_guardrail_evidence_artifacts.py

validate-stop-gate-evaluator:
	python3 tools/validate_stop_gate_evaluator.py

validate-guarded-workcell-artifact:
	python3 tools/validate_guarded_workcell_artifact.py

validate-guarded-workcell-executor:
	python3 tools/validate_guarded_workcell_executor.py

validate-guarded-invocation-artifact:
	python3 tools/validate_guarded_invocation_artifact.py

validate-guarded-invocation:
	python3 tools/validate_guarded_invocation.py

validate-agentic-pr-work-order:
	python3 tools/validate_agentic_pr_work_order.py

validate-semantic-enterprise-agent-boundary:
	python3 tools/validate_semantic_enterprise_agent_boundary.py

validate-ops-history-contracts:
	python3 tools/validate_ops_history_contracts.py

validate-action-contracts:
	python3 tools/validate_action_contracts.py

validate-agent-operation-contract:
	python3 tools/validate_agent_operation_contract.py

validate-superconscious-reasoning-import:
	python3 scripts/import_superconscious_reasoning.py examples/superconscious/deterministic

validate-agent-harness-runtime-contracts:
	python3 scripts/validate_agent_harness_runtime_contracts.py

validate-bounded-action-loop:
	python3 tools/check_bounded_action_loop.py

agentplane-evidence-receipt-composition-tier2-binding-ci:
	python3 -m json.tool schemas/composition/agentplane-evidence-receipt-composition-tier2-binding.v1.json >/dev/null
	python3 -m json.tool tests/fixtures/composition/agentplane-evidence-receipt-composition-tier2-binding.synthetic.json >/dev/null
	python3 -m json.tool tests/fixtures/composition/agentplane-evidence-receipt-composition-tier2-binding.runtime-field.invalid.synthetic.json >/dev/null
	python3 tools/check_agentplane_evidence_receipt_composition_tier2_binding.py tests/fixtures/composition/agentplane-evidence-receipt-composition-tier2-binding.synthetic.json
	! python3 tools/check_agentplane_evidence_receipt_composition_tier2_binding.py tests/fixtures/composition/agentplane-evidence-receipt-composition-tier2-binding.runtime-field.invalid.synthetic.json

lawful-learning-phase9-contract-ci:
	python3 -m json.tool schemas/receipts/lawful-learning-receipt-classes.v1.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-alignment-check.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-circuit-admission.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-decision-emission.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-replay-blackboxing.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-alignment-check.missing-replay-seal.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-alignment-check.semantic-verification.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/lawful-learning-alignment-check.policy-overwrite.invalid.json >/dev/null
	python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-alignment-check.valid.json
	python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-circuit-admission.valid.json
	python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-decision-emission.valid.json
	python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-replay-blackboxing.valid.json
	! python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-alignment-check.missing-replay-seal.invalid.json
	! python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-alignment-check.semantic-verification.invalid.json
	! python3 tools/check_lawful_learning_phase9_receipts.py tests/fixtures/receipts/lawful-learning-alignment-check.policy-overwrite.invalid.json

validate-evidence-receipt-binding:
	python3 tools/validate_evidence_receipt_binding.py

validate-semantic-activation-receipt:
	python3 -m json.tool schemas/receipts/semantic-activation-receipt.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.divergence-admitted.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.divergence-fail-closed.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-context-divergence.chain.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.missing-activation-bundle-hash.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.missing-graph-snapshot.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.missing-policy-bundle.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.missing-replay-artifact.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.missing-required-edge-evidence.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/semantic-activation-receipt.missing-admission-decision.invalid.json >/dev/null
	python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.valid.json
	python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.divergence-admitted.valid.json
	python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.divergence-fail-closed.valid.json
	python3 tools/validate_semantic_activation_context_divergence.py tests/fixtures/receipts/semantic-activation-context-divergence.chain.json
	! python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.missing-activation-bundle-hash.invalid.json
	! python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.missing-graph-snapshot.invalid.json
	! python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.missing-policy-bundle.invalid.json
	! python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.missing-replay-artifact.invalid.json
	! python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.missing-required-edge-evidence.invalid.json
	! python3 tools/validate_semantic_activation_receipt.py tests/fixtures/receipts/semantic-activation-receipt.missing-admission-decision.invalid.json

validate-governed-run-contract:
	python3 -m json.tool schemas/runs/governed-run-contract.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/governed-run-contract.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/governed-run-contract.missing-policy.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/governed-run-contract.missing-budget.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/governed-run-contract.verifierless-mutation.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/governed-run-contract.absolute-path.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/governed-run-contract.missing-authority-grant.invalid.json >/dev/null
	python3 tools/validate_governed_run_contract.py tests/fixtures/runs/governed-run-contract.valid.json
	! python3 tools/validate_governed_run_contract.py tests/fixtures/runs/governed-run-contract.missing-policy.invalid.json
	! python3 tools/validate_governed_run_contract.py tests/fixtures/runs/governed-run-contract.missing-budget.invalid.json
	! python3 tools/validate_governed_run_contract.py tests/fixtures/runs/governed-run-contract.verifierless-mutation.invalid.json
	! python3 tools/validate_governed_run_contract.py tests/fixtures/runs/governed-run-contract.absolute-path.invalid.json
	! python3 tools/validate_governed_run_contract.py tests/fixtures/runs/governed-run-contract.missing-authority-grant.invalid.json

validate-preflight-receipt:
	python3 -m json.tool schemas/receipts/preflight-receipt.v0.1.schema.json >/dev/null
	python3 tools/sp_run.py preflight tests/fixtures/runs/governed-run-contract.valid.json --generated-at 2026-05-22T12:20:00Z --output /tmp/agentplane-preflight-pass.json
	python3 tools/validate_preflight_receipt.py /tmp/agentplane-preflight-pass.json
	python3 tools/sp_run.py preflight tests/fixtures/runs/governed-run-contract.open-network.review.json --generated-at 2026-05-22T12:21:00Z --output /tmp/agentplane-preflight-review.json
	python3 tools/validate_preflight_receipt.py /tmp/agentplane-preflight-review.json

validate-attempt-admission-receipt:
	python3 -m json.tool schemas/receipts/attempt-admission-receipt.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/attempt-admission-receipt.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/attempt-admission-receipt.budget-exceeded.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/attempt-admission-receipt.safety-block.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/attempt-admission-receipt.authority-suspended.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/attempt-admission-receipt.require-review-invalid-admit.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/attempt-admission-receipt.fail-closed-missing-reason.invalid.json >/dev/null
	python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.valid.json
	! python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.budget-exceeded.invalid.json
	! python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.safety-block.invalid.json
	! python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.authority-suspended.invalid.json
	! python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.require-review-invalid-admit.invalid.json
	! python3 tools/validate_attempt_admission_receipt.py tests/fixtures/receipts/attempt-admission-receipt.fail-closed-missing-reason.invalid.json

validate-verification-execution-receipt:
	python3 -m json.tool schemas/receipts/verification-execution-receipt.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.completed.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.missing-admission-ref.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.rejected-admission.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.require-review-admission.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.non-allowlisted-command.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.open-mode.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/verification-execution-receipt.write-mode.invalid.json >/dev/null
	python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.completed.valid.json
	! python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.missing-admission-ref.invalid.json
	! python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.rejected-admission.invalid.json
	! python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.require-review-admission.invalid.json
	! python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.non-allowlisted-command.invalid.json
	! python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.open-mode.invalid.json
	! python3 tools/validate_verification_execution_receipt.py tests/fixtures/receipts/verification-execution-receipt.write-mode.invalid.json

validate-synthetic-verification-receipt:
	python3 tools/build_synthetic_verification_receipt.py \
		--output /tmp/agentplane-synthetic-verification-receipt.json \
		--execution-id verification-execution-receipt:synthetic-alpha-001 \
		--run-id governed-run-alpha-001 \
		--attempt-id attempt:governed-run-alpha-001:001 \
		--governed-run-contract-ref governed-run-contract:governed-run-alpha-001 \
		--admission-receipt-ref attempt-admission-receipt:governed-run-alpha-001:001 \
		--preflight-receipt-ref preflight-receipt:governed-run-alpha-001 \
		--authority-state-ref agent-authority-current-state:agent-alpha:active
	python3 tools/validate_verification_execution_receipt.py /tmp/agentplane-synthetic-verification-receipt.json
	python3 -m pytest -q tools/tests/test_synthetic_verification_receipt.py

validate-governed-runner-v0-2-contract-chain:
	python3 -m json.tool tests/fixtures/chains/governed-runner-v0.2-contract-chain.valid.json >/dev/null
	python3 tools/validate_governed_runner_v0_2_contract_chain.py tests/fixtures/chains/governed-runner-v0.2-contract-chain.valid.json
	python3 -m pytest -q tools/tests/test_governed_runner_v0_2_contract_chain.py

validate-budget-settlement-receipt:
	python3 -m json.tool schemas/receipts/budget-settlement-receipt.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/budget-settlement-receipt.settled.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/budget-settlement-receipt.overrun.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/budget-settlement-receipt.missing-admission-ref.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/budget-settlement-receipt.missing-actuals.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/budget-settlement-receipt.negative-actual.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/budget-settlement-receipt.hidden-overrun.invalid.json >/dev/null
	python3 tools/validate_budget_settlement_receipt.py tests/fixtures/receipts/budget-settlement-receipt.settled.valid.json
	python3 tools/validate_budget_settlement_receipt.py tests/fixtures/receipts/budget-settlement-receipt.overrun.valid.json
	! python3 tools/validate_budget_settlement_receipt.py tests/fixtures/receipts/budget-settlement-receipt.missing-admission-ref.invalid.json
	! python3 tools/validate_budget_settlement_receipt.py tests/fixtures/receipts/budget-settlement-receipt.missing-actuals.invalid.json
	! python3 tools/validate_budget_settlement_receipt.py tests/fixtures/receipts/budget-settlement-receipt.negative-actual.invalid.json
	! python3 tools/validate_budget_settlement_receipt.py tests/fixtures/receipts/budget-settlement-receipt.hidden-overrun.invalid.json

validate-rollback-receipts:
	python3 -m json.tool schemas/receipts/rollback-boundary.v0.1.schema.json >/dev/null
	python3 -m json.tool schemas/receipts/rollback-result.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/rollback-boundary.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/rollback-boundary.path-escape.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/rollback-result.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/rollback-result.failed-missing-error.invalid.json >/dev/null
	python3 tools/validate_rollback_receipts.py boundary tests/fixtures/receipts/rollback-boundary.valid.json
	! python3 tools/validate_rollback_receipts.py boundary tests/fixtures/receipts/rollback-boundary.path-escape.invalid.json
	python3 tools/validate_rollback_receipts.py result tests/fixtures/receipts/rollback-result.valid.json
	! python3 tools/validate_rollback_receipts.py result tests/fixtures/receipts/rollback-result.failed-missing-error.invalid.json

validate-run-dossier:
	python3 -m json.tool schemas/runs/run-dossier.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/run-dossier/run-dossier.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/runs/run-dossier/run-dossier.ready-missing.invalid.json >/dev/null
	python3 tools/validate_run_dossier.py tests/fixtures/runs/run-dossier/run-dossier.valid.json
	! python3 tools/validate_run_dossier.py tests/fixtures/runs/run-dossier/run-dossier.ready-missing.invalid.json
	python3 tools/build_run_dossier.py tests/fixtures/runs/run-dossier/run --generated-at 2026-05-22T12:10:00Z --output /tmp/agentplane-run-dossier.generated.json
	python3 tools/validate_run_dossier.py /tmp/agentplane-run-dossier.generated.json

validate-governed-runner-readonly:
	python3 tools/run_governed_runner_smoke.py --output-dir /tmp/agentplane-governed-runner-smoke --generated-at 2026-05-22T12:45:00Z
	python3 tools/sp_run.py list --runs-root /tmp/agentplane-governed-runner-smoke >/tmp/agentplane-run-list.json
	python3 tools/sp_run.py status /tmp/agentplane-governed-runner-smoke/run >/tmp/agentplane-run-status.json
	python3 tools/sp_run.py inspect /tmp/agentplane-governed-runner-smoke/run >/tmp/agentplane-run-inspection.json
	python3 tools/governed_runner_tool_surface.py list-tools >/tmp/agentplane-tool-list.json
	python3 tools/governed_runner_tool_surface.py call governed_runner.doctor --args-json '{}' >/tmp/agentplane-tool-doctor.json
	python3 tools/sp_run.py tool list-tools >/tmp/agentplane-sp-run-tool-list.json

validate-workroom-context-evidence:
	python3 tools/validate_workroom_context_evidence.py

validate-wallguard-collaboration-admission:
	python3 -m json.tool schemas/receipts/wallguard-collaboration-admission.v0.1.schema.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/wallguard-collaboration-admission.same-wall.valid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/wallguard-collaboration-admission.cross-wall.invalid.json >/dev/null
	python3 -m json.tool tests/fixtures/receipts/wallguard-collaboration-admission.missing-context.invalid.json >/dev/null
	python3 tools/validate_wallguard_collaboration_admission.py

test:
	python3 -m pytest -q tools/tests
.PHONY: validate-workspace-prophet-control-receipt validate-prophet-mesh-agentplane-adapter
validate-workspace-prophet-control-receipt:
	python3 tools/validate_workspace_prophet_control_receipt.py

.PHONY: validate-health-ai-control-receipt validate-prophet-mesh-agentplane-adapter
validate-health-ai-control-receipt:
	python3 tools/validate_health_ai_control_receipt.py

validate-prophet-mesh-agentplane-adapter:
	python3 -m json.tool contracts/prophet-mesh/prophet-mesh-agentplane-adapter.v0.1.json >/dev/null
	python3 tools/validate_prophet_mesh_agentplane_adapter.py

validate-civic-stack-runtime-evidence:
	python3 -m json.tool schemas/civic-stack-run-capsule.schema.v0.1.json >/dev/null
	python3 tools/validate_civic_stack_runtime_evidence.py

validate-conversational-evidence:
	python3 -m json.tool schemas/conversational-action-evidence.schema.v0.1.json >/dev/null
	python3 -m json.tool schemas/conversational-replay-record.schema.v0.1.json >/dev/null
	python3 tools/validate_conversational_evidence.py

validate-concept-to-artifact-lineage:
	python3 -m json.tool schemas/concept-to-artifact-lineage-receipt.schema.v0.1.json >/dev/null
	python3 tools/validate_concept_to_artifact_lineage.py

validate-model-routing-lane-receipts:
	python3 -m json.tool schemas/model-routing-lane-decision-receipt.schema.v0.1.json >/dev/null
	python3 tools/validate_model_routing_lane_receipts.py

validate-shir-governed-chain-job:
	python3 -m json.tool schemas/shir-governed-chain-job.schema.v0.1.json >/dev/null
	python3 tools/validate_shir_governed_chain_job.py

validate-device-actuation-boundary:
	python3 -m json.tool schemas/device-actuation-boundary-receipt.schema.v0.1.json >/dev/null
	python3 tools/validate_device_actuation_boundary.py

validate-reasoning-run-evidence:
	python3 -m json.tool schemas/reasoning-run-evidence-receipt.schema.v0.1.json >/dev/null
	python3 tools/validate_reasoning_run_evidence.py

validate-graph-aware-work-orders:
	python3 -m json.tool schemas/graph-aware-work-order.schema.v0.1.json >/dev/null
	python3 tools/validate_graph_aware_work_orders.py

validate-orggov-work-order-evidence-bridge:
	python3 -m json.tool schemas/orggov-work-order-evidence-bridge.schema.v0.1.json >/dev/null
	python3 tools/validate_orggov_work_order_evidence_bridge.py

validate-substrate-trust-gates:
	python3 -m json.tool schemas/substrate-trust-gate.schema.v0.1.json >/dev/null
	python3 tools/validate_substrate_trust_gates.py

validate-workcell-stop-gates:
	python3 -m json.tool schemas/human-override-artifact.schema.v0.1.json >/dev/null
	python3 -m json.tool schemas/guardrail-replay-artifact.schema.v0.1.json >/dev/null
	python3 tools/validate_workcell_stop_gates.py

validate-rollback-restore:
	python3 -m json.tool schemas/rollback-restore-request.schema.v0.1.json >/dev/null
	python3 -m json.tool schemas/rollback-restore-receipt.schema.v0.1.json >/dev/null
	python3 tools/validate_rollback_restore.py

validate-agentic-runtime-state:
	python3 -m json.tool schemas/agentic-runtime-state.schema.v0.1.json >/dev/null
	python3 tools/validate_agentic_runtime_state.py

validate-wallguard-collaboration-gate:
	python3 -m json.tool schemas/receipts/wallguard-collaboration-admission.v0.1.schema.json >/dev/null
	cd tools && python3 validate_wallguard_collaboration_gate.py

validate-agent-cycle-health:
	python3 tools/validate_agent_cycle_health.py

validate-authority-dependency-evidence:
	python3 tools/validate_authority_dependency_evidence.py

validate-prometheus-sr:
	python3 tools/validate_prometheus_sr.py

validate-reasoning-failure-traces:
	python3 tools/validate_reasoning_failure_traces.py
