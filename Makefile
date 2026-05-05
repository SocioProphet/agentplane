.PHONY: validate test validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-agentic-pr-work-order

validate: validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-agentic-pr-work-order
	python3 tools/validate_execution_timing.py

validate-governance-context:
	python3 scripts/verify_governance_context.py

validate-lattice-data-governai-execution-refs:
	python3 tools/validate_lattice_data_governai_execution_refs.py

validate-lattice-runtime-profile-refs:
	python3 tools/validate_lattice_runtime_profile_refs.py

validate-network-native-assistant-evidence:
	python3 tools/validate_network_native_assistant_evidence.py

validate-agentic-pr-work-order:
	python3 tools/validate_agentic_pr_work_order.py

test:
	python3 -m pytest -q tools/tests
