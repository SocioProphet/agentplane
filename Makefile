.PHONY: validate test

validate:
	python3 tools/validate_execution_timing.py

test:
	python3 -m pytest -q tools/tests
