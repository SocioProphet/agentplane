.PHONY: help ingest validate

help:
	@echo "Targets:"
	@echo "  make ingest   - extract _archives/Archive.zip into spine/"
	@echo "  make validate - run hygiene + license validation over spine/"

ingest:
	python3 scripts/ingest_archives.py --archive _archives/Archive.zip

validate:
	python3 scripts/validate_spine.py
