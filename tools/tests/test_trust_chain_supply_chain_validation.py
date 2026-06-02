from __future__ import annotations

import json
from pathlib import Path

from tools.validate_trust_chain_supply_chain_validation import main as validate_trust_chain_supply_chain_validation


ROOT = Path(__file__).resolve().parents[2]
VALID_FIXTURE = ROOT / "tests" / "fixtures" / "trust-chain" / "supply-chain-validation.valid.json"
BLOCKED_FIXTURE = ROOT / "tests" / "fixtures" / "trust-chain" / "supply-chain-validation.blocked.json"


def test_trust_chain_supply_chain_validation_artifacts_validate() -> None:
    assert validate_trust_chain_supply_chain_validation() == 0


def test_valid_supply_chain_artifact_allows_execution_and_promotion() -> None:
    fixture = json.loads(VALID_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["decision"] == "validated"
    assert fixture["effects"]["execution_allowed"] is True
    assert fixture["effects"]["promotion_allowed"] is True
    assert fixture["effects"]["repair_required"] is False
    assert fixture["effects"]["human_review_required"] is False


def test_blocked_supply_chain_artifact_blocks_execution_and_requires_repair() -> None:
    fixture = json.loads(BLOCKED_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["decision"] == "blocked"
    assert fixture["effects"]["execution_allowed"] is False
    assert fixture["effects"]["promotion_allowed"] is False
    assert fixture["effects"]["repair_required"] is True
    assert fixture["effects"]["human_review_required"] is True
    assert fixture["remediation"]
