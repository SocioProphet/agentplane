from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.durablegraph.control_pin import ControlPinError, validate_control_pin


MANIFEST = {
    "canonical_repository": "SocioProphet/socioprophet-standards-storage",
    "canonical_package_path": "examples/control-matrix/v3",
    "canonical_schema_path": "schemas/control-matrix",
    "version": "v3",
    "status": "seeded-import-lane",
    "expected_bundles": {
        "policy": "policy/imports/control-matrix/compiled_policy_bundle_v3.json",
        "monitor": "monitors/generated/control-matrix/compiled_monitor_bundle_v3.json",
        "test": "tests/generated/control-matrix/compiled_test_bundle_v3.json"
    }
}


def write_manifest(repo_root: Path) -> None:
    target = repo_root / "policy/imports/control-matrix/manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")


def test_control_pin_fails_closed_without_compiled_bundles(tmp_path: Path) -> None:
    write_manifest(tmp_path)

    with pytest.raises(ControlPinError):
        validate_control_pin(tmp_path)


def test_control_pin_passes_when_expected_bundles_exist(tmp_path: Path) -> None:
    write_manifest(tmp_path)

    for relpath in MANIFEST["expected_bundles"].values():
        target = tmp_path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n", encoding="utf-8")

    manifest = validate_control_pin(tmp_path)
    assert manifest.version == "v3"
