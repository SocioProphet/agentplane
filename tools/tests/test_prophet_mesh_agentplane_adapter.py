from __future__ import annotations

import json
from pathlib import Path

from tools.validate_prophet_mesh_agentplane_adapter import validate

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "contracts" / "prophet-mesh" / "prophet-mesh-agentplane-adapter.v0.1.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_prophet_mesh_agentplane_adapter_validates() -> None:
    assert validate(_load_fixture()) == []


def test_rejects_missing_memory_scope() -> None:
    fixture = _load_fixture()
    fixture["request_projection"]["memory_scope"] = ""
    errors = validate(fixture)
    assert any("memory_scope" in error for error in errors)


def test_rejects_email_without_review() -> None:
    fixture = _load_fixture()
    fixture["request_projection"]["operator_review_required"] = False
    errors = validate(fixture)
    assert any("email_reply" in error and "review" in error for error in errors)


def test_rejects_enabled_effect_mode() -> None:
    fixture = _load_fixture()
    fixture["request_projection"]["effect_enabled"] = True
    errors = validate(fixture)
    assert any("effect_enabled" in error for error in errors)


def test_rejects_missing_artifact_requirement() -> None:
    fixture = _load_fixture()
    fixture["required_agentplane_artifacts"].remove("replay_artifact")
    errors = validate(fixture)
    assert any("required_agentplane_artifacts" in error for error in errors)
