.PHONY: validate test validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-agent-operation-contract

validate: validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-agent-operation-contract
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

validate-agent-operation-contract:
	python3 tools/validate_agent_operation_contract.py

test:
	python3 -m pytest -q tools/tests
