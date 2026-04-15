from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


class ControlImportManifest(BaseModel):
    canonical_repository: str
    canonical_package_path: str
    canonical_schema_path: str
    version: str
    expected_bundles: dict[str, str]
    status: str


class ControlPinError(RuntimeError):
    """Raised when the imported control package is missing or inconsistent."""


def load_control_import_manifest(repo_root: Path) -> ControlImportManifest:
    manifest_path = repo_root / "policy/imports/control-matrix/manifest.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ControlImportManifest.model_validate(raw)


def validate_control_pin(repo_root: Path) -> ControlImportManifest:
    manifest = load_control_import_manifest(repo_root)

    missing_paths = [
        relpath
        for relpath in manifest.expected_bundles.values()
        if not (repo_root / relpath).exists()
    ]
    if missing_paths:
        raise ControlPinError(
            "compiled control bundles are missing: " + ", ".join(missing_paths)
        )

    return manifest
