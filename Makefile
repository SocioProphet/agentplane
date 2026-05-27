.PHONY: validate test validate-sr validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-semantic-enterprise-agent-boundary validate-ops-history-contracts validate-action-contracts validate-agent-operation-contract validate-superconscious-reasoning-import validate-agent-harness-runtime-contracts validate-bounded-action-loop agentplane-evidence-receipt-composition-tier2-binding-ci lawful-learning-phase9-contract-ci validate-evidence-receipt-binding validate-semantic-activation-receipt validate-governed-run-contract validate-attempt-admission-receipt

validate: validate-sr validate-governance-context validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs validate-network-native-assistant-evidence validate-guardrail-evidence-artifacts validate-stop-gate-evaluator validate-guarded-workcell-artifact validate-guarded-workcell-executor validate-guarded-invocation-artifact validate-guarded-invocation validate-agentic-pr-work-order validate-semantic-enterprise-agent-boundary validate-ops-history-contracts validate-action-contracts validate-agent-operation-contract validate-superconscious-reasoning-import validate-agent-harness-runtime-contracts validate-bounded-action-loop agentplane-evidence-receipt-composition-tier2-binding-ci lawful-learning-phase9-contract-ci validate-evidence-receipt-binding validate-semantic-activation-receipt validate-governed-run-contract validate-attempt-admission-receipt
	python3 tools/validate_execution_timing.py

validate-sr:
	@echo "--- JSON Schema validation ---"
	python3 scripts/validate_schema.py --schema schemas/symbolic-regression/sr-run-artifact.schema.json --fixtures tests/fixtures/symbolic-regression/
	@echo "--- Replay hash recomputation ---"
	python3 scripts/validate_replay_hash.py tests/fixtures/symbolic-regression/sr-run-artifact.valid.json
	python3 scripts/validate_replay_hash.py tests/fixtures/symbolic-regression/reject_tampered_replay_hash.json --expect-invalid
	@echo "--- Replay reference resolution ---"
	python3 scripts/validate_replay_ref.py tests/fixtures/symbolic-regression/reject_missing_replay_on_proposal.proposal.json --fixture-store tests/fixtures/symbolic-regression/store/ --expect-invalid
	@echo "--- SINDy controlAuthority gate ---"
	python3 scripts/validate_schema.py --schema schemas/symbolic-regression/sr-run-artifact.schema.json --fixture tests/fixtures/symbolic-regression/reject-sindy-control-authority-true.json --expect-invalid

validate-governance-context:
	python3 scripts/verify_governance_context.py
