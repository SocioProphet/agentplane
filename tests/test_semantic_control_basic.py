from __future__ import annotations

import json
from pathlib import Path

from scripts.semantic_control import canonical_profile_bytes, derive_projection, profile_sha256, verify_expiry


def test_canonical_profile_bytes_ignores_embedded_hash(tmp_path: Path) -> None:
    profile = {
        "metadata": {
            "profileSha256": "abc",
            "issuedAt": "2099-01-01T00:00:00Z",
            "expiresAt": "2099-02-01T00:00:00Z",
        },
        "spec": {"runtimeProjection": {"lane": "staging", "toolBudget": 5}},
    }
    first = canonical_profile_bytes(profile)
    profile["metadata"]["profileSha256"] = "def"
    second = canonical_profile_bytes(profile)
    assert first == second
    assert profile_sha256(profile)


def test_projection_override_wins() -> None:
    profile = {"spec": {"runtimeProjection": {"lane": "staging", "toolBudget": 5}}}
    override = {"projectionOverride": {"toolBudget": 9, "memoryScope": "local-only"}}
    projection = derive_projection(profile, override)
    assert projection["lane"] == "staging"
    assert projection["toolBudget"] == 9
    assert projection["memoryScope"] == "local-only"


def test_verify_expiry_reports_not_yet_valid() -> None:
    profile = {
        "metadata": {
            "issuedAt": "2999-01-01T00:00:00Z",
            "expiresAt": "2999-02-01T00:00:00Z",
        }
    }
    ok, status = verify_expiry(profile)
    assert ok is False
    assert status == "not yet valid"
