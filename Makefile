.PHONY: validate test validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs

validate: validate-lattice-data-governai-execution-refs validate-lattice-runtime-profile-refs
	python3 tools/validate_execution_timing.py

validate-lattice-data-governai-execution-refs:
	python3 tools/validate_lattice_data_governai_execution_refs.py

validate-lattice-runtime-profile-refs:
	python3 tools/validate_lattice_runtime_profile_refs.py

test:
	python3 -m pytest -q tools/tests
