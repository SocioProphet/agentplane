#!/usr/bin/env python3
"""WO-4 narration fidelity: P4 comparison + P5 verdict -> signed StepGate.

Run: python3 -m pytest -q tools/tests/test_narration_fidelity_verifier.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, _TOOLS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


em = _load("trace_cfr_emitter")
ing = _load("trace_cfr_ingest")
cfg = _load("trace_cfr_cfg")
norm = _load("trace_cfr_normalize")
rh = _load("recover_hammock")
sg = _load("stopgate_artifact")
_load("step_gate")
nfv = _load("narration_fidelity_verifier")


def _pipeline(e):
    r = ing.ingest_sealed_segment(e.seal())
    assert r.ok, r.reasons
    g = cfg.build_cfg(r.events)
    return r.events, rh.recover_hammock(g, norm.normalize(g))


def _signer():
    return sg.Signer.from_seed(b"\x02" * 32, "harness-k")


def test_truthful_while_claim_is_pos_and_permits():
    e = em.TraceCfrEmitter("w")
    e.tool_call("head")
    g1 = e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    g3 = e.decision("guard", "false", "pre")
    e.terminal()
    events, rec = _pipeline(e)

    claim = {"claim_id": "c1", "covers": [g1, g3], "clause": {"primitive": "WHILE"}}
    cv = nfv.verify_claim(claim, events, rec)
    assert cv.verdict == nfv.POS, cv.reason

    art = nfv.emit_stepgate(cv, _signer())
    assert art["verdict"] == "OK"
    ok, problems = __import__("step_gate").verify_step_gate(art, sg.Keyring().add_signer(_signer()))
    assert ok, problems


def test_lying_while_vs_dowhile_is_neg_violation_with_failure_trace():
    e = em.TraceCfrEmitter("d")
    b1 = e.tool_call("body")
    e.decision("guard", "true", "post")
    e.tool_call("body")
    g2 = e.decision("guard", "false", "post")
    e.terminal()
    events, rec = _pipeline(e)

    # agent CLAIMS a pre-checked WHILE but actually ran a post-checked DO_WHILE
    claim = {"claim_id": "c2", "covers": [b1, g2], "clause": {"primitive": "WHILE"}}
    cv = nfv.verify_claim(claim, events, rec)
    assert cv.verdict == nfv.NEG, cv.reason
    assert cv.claimed_primitive == "WHILE" and cv.recovered_primitive == "DO_WHILE"

    art = nfv.emit_stepgate(cv, _signer())
    assert art["verdict"] == "VIOLATION"
    trace = nfv.reasoning_failure_trace(cv)
    assert trace["kind"] == "ReasoningFailureTrace"
    assert trace["failure_cluster"] == "GOV-NARR-STRUCT-001"


def test_claim_over_latent_decision_is_zero_never_neg():
    # a claim about a single-execution decision must NOT be charged as a lie
    e = em.TraceCfrEmitter("l")
    a = e.tool_call("a")
    e.decision("g", "true")   # latent
    b = e.tool_call("b")
    e.terminal()
    events, rec = _pipeline(e)
    claim = {"claim_id": "c3", "covers": [a, b], "clause": {"primitive": "IF"}}
    cv = nfv.verify_claim(claim, events, rec)
    assert cv.verdict == nfv.ZERO
    assert cv.reason == "RECOVERED_ZERO"


def test_unanchored_and_unstructured_claims_are_zero():
    e = em.TraceCfrEmitter("z")
    e.tool_call("x")
    e.terminal()
    events, rec = _pipeline(e)

    unanchored = {"claim_id": "u1", "clause": {"primitive": "SEQ"}}   # no covers
    assert nfv.verify_claim(unanchored, events, rec).reason == "CLAIM_UNANCHORED"

    unstructured = {"claim_id": "u2", "covers": [events[0]["event_id"], events[-1]["event_id"]]}
    cv = nfv.verify_claim(unstructured, events, rec)
    assert cv.verdict == nfv.ZERO and cv.reason == "CLAIM_UNSTRUCTURED"


def test_verify_all_wires_gates_and_traces():
    e = em.TraceCfrEmitter("m")
    b1 = e.tool_call("body")
    e.decision("guard", "true", "post")
    e.tool_call("body")
    g2 = e.decision("guard", "false", "post")
    e.terminal()
    events, rec = _pipeline(e)
    claims = [
        {"claim_id": "ok", "covers": [b1, g2], "clause": {"primitive": "DO_WHILE"}},   # truthful
        {"claim_id": "lie", "covers": [b1, g2], "clause": {"primitive": "WHILE"}},     # lie
    ]
    verdicts, gates, traces = nfv.verify_all(claims, events, rec, _signer())
    assert {v.verdict for v in verdicts} == {nfv.POS, nfv.NEG}
    assert len(gates) == 2
    assert len(traces) == 1 and traces[0]["claim_refs"] == ["lie"]
