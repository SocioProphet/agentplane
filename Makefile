.PHONY: validate test validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-agentic-ops-runtime-budget-control validate-semantic-enterprise-agent-boundary validate-ops-history-contracts agentplane-evidence-receipt-composition-tier2-binding-ci lawful-learning-phase9-contract-ci

validate: validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-agentic-ops-runtime-budget-control validate-semantic-enterprise-agent-boundary validate-ops-history-contracts agentplane-evidence-receipt-composition-tier2-binding-ci lawful-learning-phase9-contract-ci
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

validate-agentic-ops-runtime-budget-control:
	python3 tools/validate_agentic_ops_runtime_budget_control.py

validate-semantic-enterprise-agent-boundary:
	python3 tools/validate_semantic_enterprise_agent_boundary.py

validate-ops-history-contracts:
	python3 tools/validate_ops_history_contracts.py

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

test:
	python3 -m pytest -q tools/tests
