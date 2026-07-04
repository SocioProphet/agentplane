#!/usr/bin/env python3
"""§9 StepGateArtifact emission + §14.3 gate-factorization conformance.

Run: python3 -m pytest -q tools/tests/test_step_gate.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.join(_HERE, os.pardir)
sys.path.insert(0, _TOOLS)  # so step_gate can import stopgate_artifact


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


sg = _load("stopgate_artifact")
stepgate = _load("step_gate")


def _signer():
    return sg.Signer.from_seed(b"\x01" * 32, key_id="harness-k1")


def _ev():
    return [sg.Evidence(source_event_uuid="e1", evidence_hash="sha256:" + "0" * 64, layer="semantic")]


def test_emit_and_verify_roundtrip():
    s = _signer()
    kr = sg.Keyring().add_signer(s)
    art = stepgate.build_step_gate(node_id="n1", tier=1, finding="OK", evidence=_ev(), signer=s)
    ok, problems = stepgate.verify_step_gate(art, kr)
    assert ok, problems
    assert art["verdict"] == "OK"


def test_tier0_violation_short_circuits():
    s = _signer()
    art = stepgate.build_step_gate(node_id="n2", tier=0, finding="VIOLATION", evidence=_ev(), signer=s)
    assert art["verdict"] == "VIOLATION"
    assert art["short_circuit"] is True
    assert stepgate.should_short_circuit(art) is True
    # a tier-1 violation does not short-circuit (turn-level, not trajectory-level)
    art1 = stepgate.build_step_gate(node_id="n2", tier=1, finding="VIOLATION", evidence=_ev(), signer=s)
    assert art1["short_circuit"] is False


def test_finding_none_is_indeterminate():
    s = _signer()
    art = stepgate.build_step_gate(node_id="n3", tier=1, finding=None, evidence=[], signer=s)
    assert art["verdict"] == "INDETERMINATE"


# ---- §14.3 gate-factorization: v = g_H(e), model excluded from the verdict ---- #
def test_verdict_is_pure_function_of_finding_not_scores():
    # promise/progress (advisory, possibly model-emitted) MUST NOT change the verdict
    s = _signer()
    a = stepgate.build_step_gate(node_id="n", tier=1, finding="REVIEW", evidence=_ev(), signer=s,
                                 promise=0.99, progress=0.99)
    b = stepgate.build_step_gate(node_id="n", tier=1, finding="REVIEW", evidence=_ev(), signer=s,
                                 promise=0.01, progress=0.01)
    assert a["verdict"] == b["verdict"] == "REVIEW"
    assert stepgate.derive_verdict("REVIEW") == "REVIEW"  # deterministic, no side inputs


def test_model_authored_verdict_rejected():
    s = _signer()
    with pytest.raises(ValueError):
        stepgate.build_step_gate(node_id="n", tier=1, finding="OK", evidence=_ev(), signer=s,
                                 evaluated_by={"kind": "model"})


def test_tampered_artifact_fails_verification():
    s = _signer()
    kr = sg.Keyring().add_signer(s)
    art = stepgate.build_step_gate(node_id="n5", tier=0, finding="OK", evidence=_ev(), signer=s)
    art["verdict"] = "VIOLATION"  # flip the verdict post-signature
    ok, problems = stepgate.verify_step_gate(art, kr)
    assert not ok and any("signature" in p for p in problems)


def test_attribution_emitter_is_harness_pinned():
    # §14.3 also constrains AttributionIR.emitter to the harness set (const in schema)
    import json

    from jsonschema.validators import Draft202012Validator as V

    schema = json.load(open(os.path.join(_TOOLS, os.pardir, "schemas", "attribution-ir.schema.v0.1.json")))
    val = V(schema)
    assert list(val.iter_errors({"node_id": "n", "crs": 0.5, "emitter": "harness_replay_job"})) == []
    assert list(val.iter_errors({"node_id": "n", "crs": 0.5, "emitter": "model"}))  # model rejected
