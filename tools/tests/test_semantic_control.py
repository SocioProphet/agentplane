from __future__ import annotations

import copy
import datetime as dt

import pytest

from tools.validate_semantic_control import (
    SemanticControlError,
    check_replay,
    profile_sha256,
    validate_profile,
)

NOW = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)


def _base_profile() -> dict:
    return {
        "apiVersion": "sct.socioprophet.org/v0.1",
        "kind": "SCTControlProfile",
        "metadata": {
            "name": "semk-default-audience-pass",
            "version": "0.1.0",
            "issuedAt": "2026-01-01T00:00:00Z",
            "expiresAt": "2027-01-01T00:00:00Z",
            "issuer": "urn:socioprophet:agentplane:semantic-control",
            "audience": ["agentplane-ci", "agentplane-runtime"],
            "keyId": "semk-test-key-1",
            "profileSha256": "0" * 64,
            "signatureRef": "urn:socioprophet:signature:semk-test-key-1:valid",
        },
        "spec": {
            "motifs": [
                {"name": "gate", "weight": 1.0},
                {"name": "neck", "weight": 0.8},
                {"name": "chapel", "weight": 0.7},
            ],
            "runtimeProjection": {
                "lane": "staging",
                "plannerBranchBudget": 3,
                "toolBudget": 3,
                "memoryScope": "local-only",
                "disclosureScope": "bounded",
                "handoffPolicy": "mediated",
                "interruptPolicy": "standard",
                "humanGateRequired": False,
                "breakGlassAllowed": False,
                "maxRunSeconds": 600,
                "auditMode": "strict",
            },
            "delivery": {
                "mode": "mcp-sidecar",
                "authorizedAudience": ["agentplane-ci", "agentplane-runtime"],
                "failClosed": True,
                "redactionMode": "hash-only",
            },
            "deconfliction": {
                "breakGlassAllowed": False,
                "breakGlassReasonRequired": False,
                "unauthorizedTelemetry": True,
                "replayBindProfileHash": True,
            },
            "replayPolicy": {
                "bindSameHash": True,
                "allowAuthorizedSuccessor": False,
                "successorProofRequired": True,
            },
            "failMode": "deny",
        },
    }


def _finalized(profile: dict) -> dict:
    out = copy.deepcopy(profile)
    out["metadata"]["profileSha256"] = profile_sha256(out)
    return out


def _mutated(mutator) -> dict:
    profile = _base_profile()
    mutator(profile)
    return _finalized(profile)


def test_valid_profile_accepts_authorized_audience() -> None:
    profile = _finalized(_base_profile())
    result = validate_profile(profile, audience="agentplane-ci", now=NOW)
    assert result["profileRef"] == "semk-default-audience-pass"
    assert result["projection"]["memoryScope"] == "local-only"
    assert result["motifs"] == ["chapel", "gate", "neck"]


def test_expired_profile_fails_closed() -> None:
    profile = _mutated(lambda p: p["metadata"].update({"expiresAt": "2026-01-02T00:00:00Z"}))
    with pytest.raises(SemanticControlError, match="expired"):
        validate_profile(profile, audience="agentplane-ci", now=NOW)


def test_wrong_audience_fails_closed() -> None:
    def mutate(profile: dict) -> None:
        profile["metadata"]["audience"] = ["other-agent"]
        profile["spec"]["delivery"]["authorizedAudience"] = ["other-agent"]

    profile = _mutated(mutate)
    with pytest.raises(SemanticControlError, match="audience"):
        validate_profile(profile, audience="agentplane-ci", now=NOW)


def test_revoked_key_fails_closed() -> None:
    profile = _mutated(lambda p: p["metadata"].update({"keyId": "revoked-key-1"}))
    with pytest.raises(SemanticControlError, match="revoked"):
        validate_profile(profile, audience="agentplane-ci", revoked_keys={"revoked-key-1"}, now=NOW)


def test_malformed_profile_fails_shape_validation() -> None:
    profile = _finalized(_base_profile())
    profile["spec"].pop("failMode")
    with pytest.raises(SemanticControlError, match="failMode"):
        validate_profile(profile, audience="agentplane-ci", now=NOW, check_hash=False)


def test_valid_signature_with_invalid_projection_semantics_fails_mg_011() -> None:
    def mutate(profile: dict) -> None:
        profile["spec"]["runtimeProjection"]["memoryScope"] = "workspace"
        profile["spec"]["runtimeProjection"]["toolBudget"] = 12

    profile = _mutated(mutate)
    with pytest.raises(SemanticControlError, match="chapel motif"):
        validate_profile(profile, audience="agentplane-ci", now=NOW)


def test_neck_motif_cannot_expand_budget_or_disclosure() -> None:
    def mutate(profile: dict) -> None:
        profile["spec"]["runtimeProjection"]["toolBudget"] = 8
        profile["spec"]["runtimeProjection"]["disclosureScope"] = "expanded"

    profile = _mutated(mutate)
    with pytest.raises(SemanticControlError, match="neck motif"):
        validate_profile(profile, audience="agentplane-ci", now=NOW)


def test_replay_same_profile_hash_is_allowed() -> None:
    profile = _finalized(_base_profile())
    result = check_replay(profile, profile, audience="agentplane-ci", now=NOW)
    assert result["result"] == "allow"
    assert result["reason"] == "same profile hash"


def test_replay_profile_drift_without_successor_is_denied_mg_010() -> None:
    previous = _finalized(_base_profile())

    def mutate(profile: dict) -> None:
        profile["metadata"]["name"] = "semk-drift-no-successor"
        profile["spec"]["runtimeProjection"]["toolBudget"] = 4

    drift = _mutated(mutate)
    with pytest.raises(SemanticControlError, match="semantic drift denied"):
        check_replay(previous, drift, audience="agentplane-ci", now=NOW)


def test_replay_signed_authorized_successor_is_allowed_mg_012() -> None:
    previous = _finalized(_base_profile())

    def mutate(profile: dict) -> None:
        profile["metadata"]["name"] = "semk-authorized-successor"
        profile["metadata"]["version"] = "0.1.1"
        profile["spec"]["runtimeProjection"]["toolBudget"] = 4
        profile["spec"]["replayPolicy"]["allowAuthorizedSuccessor"] = True
        profile["spec"]["replayPolicy"]["authorizedSuccessorOf"] = previous["metadata"]["profileSha256"]
        profile["spec"]["replayPolicy"]["successorSignatureRef"] = "urn:socioprophet:signature:semk-test-key-1:successor"

    successor = _mutated(mutate)
    result = check_replay(previous, successor, audience="agentplane-ci", now=NOW)
    assert result["result"] == "allow"
    assert result["reason"] == "signed authorized successor"
    assert result["successorOf"] == previous["metadata"]["profileSha256"]


def test_profile_hash_detects_silent_semantic_drift() -> None:
    profile = _finalized(_base_profile())
    profile["spec"]["runtimeProjection"]["toolBudget"] = 4
    with pytest.raises(SemanticControlError, match="profileSha256"):
        validate_profile(profile, audience="agentplane-ci", now=NOW)
