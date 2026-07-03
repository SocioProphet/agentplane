"""Invariant, verdict, signing, and schema-conformance tests for the formal
StopGateArtifact reference implementation (spec v0.1)."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ed25519 signing is intrinsic to the artifact; skip the suite where the dep is absent.
pytest.importorskip("cryptography")

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "stopgate_artifact.py"
spec = importlib.util.spec_from_file_location("stopgate_artifact", MODULE_PATH)
assert spec is not None and spec.loader is not None
sg = importlib.util.module_from_spec(spec)
sys.modules["stopgate_artifact"] = sg
spec.loader.exec_module(sg)

SEED = bytes.fromhex("00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff")


def make_signer() -> "sg.Signer":
    return sg.Signer.from_seed(SEED, "test-key-2026")


def make_keyring(signer: "sg.Signer") -> "sg.Keyring":
    return sg.Keyring().add_signer(signer)


def semantic_evidence(mode: str = "presence", layer: str = "semantic") -> "sg.Evidence":
    return sg.Evidence(
        source_event_uuid="evt-1",
        evidence_hash=sg.sha256_evidence("payload"),
        layer=layer,
        signal="regex:/build failed/i",
        mode=mode,
    )


def emit(finding, **overrides):
    signer = overrides.pop("signer", None) or make_signer()
    kwargs = dict(
        finding=finding,
        evidence=overrides.pop("evidence", [semantic_evidence()]),
        signer=signer,
        gate_id="build-green-before-push",
        session_id="sess-1",
        workcell_id="wc-1",
        subject=["git push"],
        predicate="build.exit_code == 0",
        evaluated_by={"component": "agentplane.stopgate", "version": "0.1.0", "kind": "deterministic-harness"},
        lift_authority="policy-fabric",
        window_start="2026-06-10T18:22:35Z",
        window_end="2026-06-10T18:22:38Z",
        evaluated_at="2026-06-10T18:22:39Z",
        predicate_layer="semantic",
    )
    kwargs.update(overrides)
    artifact, notes = sg.evaluate(**kwargs)
    return artifact, notes, signer


# --------------------------------------------------------------------------- #
# §4 verdict domain + disposition
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "finding,verdict,disposition",
    [
        ("OK", "PASS", "permit"),
        ("VIOLATION", "FAIL", "deny"),
        ("REVIEW", "REVIEW", "deny-pending-human"),
        (None, "INDETERMINATE", "deny-require-override"),
    ],
)
def test_verdict_mapping_and_disposition(finding, verdict, disposition):
    artifact, _, signer = emit(finding)
    assert artifact["verdict"] == verdict
    result = sg.verify_artifact(artifact, make_keyring(signer))
    assert result.disposition == disposition


def test_review_never_permits():
    artifact, _, signer = emit("REVIEW")
    result = sg.verify_artifact(artifact, make_keyring(signer))
    assert result.disposition != "permit"


# --------------------------------------------------------------------------- #
# 5.1 model-exclusion
# --------------------------------------------------------------------------- #
def test_5_1_build_rejects_model_authority():
    with pytest.raises(ValueError, match="5.1"):
        sg.build_unsigned(
            gate_id="g", session_id="s", workcell_id="w", subject=["x"], predicate="p",
            verdict="PASS", evidence=[semantic_evidence()],
            evaluated_by={"component": "gpt", "version": "1", "kind": "model"},
            evaluated_at="2026-06-10T18:22:39Z",
            window_start="2026-06-10T18:22:35Z", window_end="2026-06-10T18:22:38Z",
            lift_authority="policy-fabric",
        )


def test_5_1_verify_flags_model_authority():
    artifact, _, signer = emit("OK")
    tampered = copy.deepcopy(artifact)
    tampered["evaluated_by"]["kind"] = "model"
    result = sg.verify_artifact(tampered, make_keyring(signer))
    assert not result.ok
    assert any("5.1" in v for v in result.violations)


# --------------------------------------------------------------------------- #
# 5.2 temporal precedence
# --------------------------------------------------------------------------- #
def test_5_2_build_rejects_evidence_after_evaluation():
    with pytest.raises(ValueError, match="5.2"):
        emit("OK", window_end="2026-06-10T18:22:40Z", evaluated_at="2026-06-10T18:22:39Z")


def test_5_2_verify_flags_action_before_evidence_window_end():
    artifact, _, signer = emit("OK")
    result = sg.verify_artifact(artifact, make_keyring(signer), action_start="2026-06-10T18:22:37Z")
    assert not result.ok
    assert any("5.2" in v for v in result.violations)


def test_5_2_verify_flags_evidence_observed_outside_window():
    ev = sg.Evidence("evt", sg.sha256_evidence("p"), "semantic", observed_at="2026-06-10T19:00:00Z")
    artifact, _, signer = emit("OK", evidence=[ev])
    result = sg.verify_artifact(artifact, make_keyring(signer))
    assert any("5.2" in v for v in result.violations)


# --------------------------------------------------------------------------- #
# 5.3 layer binding
# --------------------------------------------------------------------------- #
def test_5_3_transport_evidence_cannot_satisfy_semantic_predicate():
    artifact, notes, signer = emit("OK", evidence=[semantic_evidence(layer="transport")])
    # Raw PASS degrades to REVIEW because no semantic-layer evidence backs it.
    assert artifact["verdict"] == "REVIEW"
    assert any("5.3" in n for n in notes)
    result = sg.verify_artifact(artifact, make_keyring(signer))
    assert result.disposition == "deny-pending-human"


def test_5_3_verify_flags_forged_pass_without_semantic_evidence():
    signer = make_signer()
    # Forge a PASS whose only evidence is transport, then re-sign it (attacker with key).
    forged = sg.build_unsigned(
        gate_id="g", session_id="s", workcell_id="w", subject=["x"], predicate="p",
        verdict="PASS", evidence=[semantic_evidence(layer="transport")],
        evaluated_by={"component": "c", "version": "1", "kind": "deterministic-harness"},
        evaluated_at="2026-06-10T18:22:39Z",
        window_start="2026-06-10T18:22:35Z", window_end="2026-06-10T18:22:38Z",
        lift_authority="policy-fabric",
    )
    forged = sg.sign_artifact(forged, signer)
    result = sg.verify_artifact(forged, make_keyring(signer))
    assert result.disposition == "deny"  # permit downgraded
    assert any("5.3" in v for v in result.violations)


# --------------------------------------------------------------------------- #
# 5.4 completeness-gated closed-world
# --------------------------------------------------------------------------- #
def test_5_4_absence_without_completeness_degrades_to_review():
    artifact, notes, signer = emit("VIOLATION", evidence=[semantic_evidence(mode="absence")])
    assert artifact["verdict"] == "REVIEW"
    assert any("5.4" in n for n in notes)


def test_5_4_absence_with_valid_completeness_holds_fail():
    att = sg.CompletenessAttestation(
        asserted=True, basis="no gap markers", attested_by="agentplane.recorder@0.1.0"
    )
    artifact, notes, signer = emit(
        "VIOLATION", evidence=[semantic_evidence(mode="absence")], completeness=att
    )
    assert artifact["verdict"] == "FAIL"
    assert notes == []
    result = sg.verify_artifact(artifact, make_keyring(signer))
    assert result.ok and result.disposition == "deny"


def test_5_4_verify_flags_forged_absence_pass_without_completeness():
    signer = make_signer()
    forged = sg.build_unsigned(
        gate_id="g", session_id="s", workcell_id="w", subject=["x"], predicate="p",
        verdict="FAIL", evidence=[semantic_evidence(mode="absence")],
        evaluated_by={"component": "c", "version": "1", "kind": "deterministic-harness"},
        evaluated_at="2026-06-10T18:22:39Z",
        window_start="2026-06-10T18:22:35Z", window_end="2026-06-10T18:22:38Z",
        lift_authority="policy-fabric",
    )
    forged = sg.sign_artifact(forged, signer)
    result = sg.verify_artifact(forged, make_keyring(signer))
    assert any("5.4" in v for v in result.violations)


def test_5_4_signed_completeness_attestation_verifies():
    recorder = sg.Signer.from_seed(bytes(range(32)), "recorder-key")
    att_body = {"asserted": True, "basis": "counter continuous", "attested_by": "recorder-key"}
    att = sg.CompletenessAttestation(
        asserted=True, basis="counter continuous", attested_by="recorder-key",
        signature=recorder.signature_block(sg.canonical_bytes(att_body)),
    )
    artifact, notes, signer = emit(
        "VIOLATION", evidence=[semantic_evidence(mode="absence")], completeness=att,
        keyring=sg.Keyring().add_signer(recorder),
    )
    assert artifact["verdict"] == "FAIL"
    kr = sg.Keyring().add_signer(signer).add_signer(recorder)
    assert sg.verify_artifact(artifact, kr).ok


# --------------------------------------------------------------------------- #
# 5.5 override is attributed
# --------------------------------------------------------------------------- #
def test_5_5_override_is_attributed_and_verifies():
    denied, _, signer = emit("VIOLATION")
    assert denied["verdict"] == "FAIL"
    override = sg.build_override(
        denied, operator={"id": "mdheller", "display_name": "M. Heller"},
        signer=signer, basis="hotfix authorized verbally",
    )
    assert override["evaluated_by"]["kind"] == "human-authority"
    assert override["operator"]["id"] == "mdheller"
    assert override["override_of"] == sg.artifact_id(denied)
    result = sg.verify_artifact(override, make_keyring(signer))
    assert result.ok and result.disposition == "permit"


def test_5_5_override_requires_operator():
    denied, _, signer = emit("VIOLATION")
    with pytest.raises(ValueError, match="5.5"):
        sg.build_override(denied, operator={}, signer=signer, basis="x")


def test_5_5_verify_flags_override_missing_attribution():
    denied, _, signer = emit("VIOLATION")
    override = sg.build_override(
        denied, operator={"id": "op"}, signer=signer, basis="x"
    )
    tampered = copy.deepcopy(override)
    del tampered["override_of"]
    tampered = sg.sign_artifact(tampered, signer)  # re-sign so only 5.5 fails
    result = sg.verify_artifact(tampered, make_keyring(signer))
    assert any("5.5" in v for v in result.violations)


# --------------------------------------------------------------------------- #
# Signing
# --------------------------------------------------------------------------- #
def test_signature_round_trip():
    artifact, _, signer = emit("OK")
    assert sg.verify_artifact(artifact, make_keyring(signer)).signature_valid


def test_tampered_payload_breaks_signature():
    artifact, _, signer = emit("OK")
    tampered = copy.deepcopy(artifact)
    tampered["subject"] = ["git push", "rm -rf /"]
    result = sg.verify_artifact(tampered, make_keyring(signer))
    assert not result.signature_valid
    assert result.disposition == "deny"


def test_unknown_key_does_not_verify():
    artifact, _, _ = emit("OK")
    other = sg.Signer.generate("someone-else")
    result = sg.verify_artifact(artifact, sg.Keyring().add_signer(other))
    assert not result.signature_valid


def test_canonicalization_is_key_order_independent():
    artifact, _, signer = emit("OK")
    reordered = dict(reversed(list(artifact.items())))
    assert sg.verify_artifact(reordered, make_keyring(signer)).signature_valid


# --------------------------------------------------------------------------- #
# Schema conformance
# --------------------------------------------------------------------------- #
def test_example_matches_schema_and_is_fail():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schemas" / "StopGateArtifact.schema.v0.1.json").read_text())
    example = json.loads((ROOT / "examples" / "stop-gate-artifact.build-green.json").read_text())
    jsonschema.validate(example, schema)
    assert example["verdict"] == "FAIL"


def test_committed_example_signature_verifies():
    example = json.loads((ROOT / "examples" / "stop-gate-artifact.build-green.json").read_text())
    pub = json.loads((ROOT / "examples" / "stop-gate-artifact.build-green.pubkey.json").read_text())
    keyring = sg.Keyring().add_b64(pub["key_id"], pub["public_b64"])
    result = sg.verify_artifact(example, keyring, action_start="2026-06-10T18:22:40Z")
    assert result.ok and result.signature_valid
    assert result.disposition == "deny"


def test_emitted_artifacts_match_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schemas" / "StopGateArtifact.schema.v0.1.json").read_text())
    for finding in ("OK", "VIOLATION", "REVIEW", None):
        artifact, _, _ = emit(finding)
        jsonschema.validate(artifact, schema)
