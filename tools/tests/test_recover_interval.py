#!/usr/bin/env python3
"""R_I interval recovery + two-engine P5 composition (WO-3, SPEC §4.3/§4.5).

Run: python3 -m pytest -q tools/tests/test_recover_interval.py
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
ri = _load("recover_interval")
nfv = _load("narration_fidelity_verifier")


def _both(e):
    r = ing.ingest_sealed_segment(e.seal())
    assert r.ok, r.reasons
    g = cfg.build_cfg(r.events)
    n = norm.normalize(g)
    return r.events, rh.recover_hammock(g, n), ri.recover_interval(g, n)


def _while(session, n_iter=2):
    e = em.TraceCfrEmitter(session)
    e.tool_call("head")
    ids = [e.decision("guard", "true", "pre")]
    e.tool_call("body")
    for _ in range(n_iter - 1):
        ids.append(e.decision("guard", "true", "pre"))
        e.tool_call("body")
    last = e.decision("guard", "false", "pre")
    e.terminal()
    return e, ids[0], last


def test_interval_recovers_while_verified_grade_with_witness():
    e, _, _ = _while("iw")
    _, _, ri_rec = _both(e)
    assert "WHILE" in ri_rec.primitives()
    assert ri_rec.engine == "interval"
    assert ri_rec.evidence_grade == "verified"           # promoted via the nesting witness
    assert ri_rec.nesting_depth["body#tool_call"] >= 1   # inside one loop


def test_two_engines_agree_pos_on_truthful_claim():
    e, a, b = _while("ta")
    events, rh_rec, ri_rec = _both(e)
    claim = {"claim_id": "c", "covers": [a, b], "clause": {"primitive": "WHILE"}}
    cv = nfv.verify_claim(claim, events, rh_rec, ri_recovery=ri_rec)
    assert cv.verdict == nfv.POS and not cv.verifier_fault


def test_two_engines_agree_neg_on_lie():
    # run DO_WHILE, claim WHILE -> both engines NEG -> composite NEG
    e = em.TraceCfrEmitter("tn")
    b1 = e.tool_call("body")
    e.decision("guard", "true", "post")
    e.tool_call("body")
    g2 = e.decision("guard", "false", "post")
    e.terminal()
    events, rh_rec, ri_rec = _both(e)
    claim = {"claim_id": "c", "covers": [b1, g2], "clause": {"primitive": "WHILE"}}
    cv = nfv.verify_claim(claim, events, rh_rec, ri_recovery=ri_rec)
    assert cv.verdict == nfv.NEG


def test_sign_disagreement_is_verifier_fault_not_violation():
    # POS from one engine, NEG from the other => VERIFIER-FAULT-001 (INDETERMINATE), never VIOLATION
    assert nfv.compose_two(nfv.POS, nfv.NEG) == nfv.INDETERMINATE
    assert nfv.compose_two(nfv.NEG, nfv.POS) == nfv.INDETERMINATE
    # and the sane cases
    assert nfv.compose_two(nfv.POS, nfv.ZERO) == nfv.POS
    assert nfv.compose_two(nfv.NEG, nfv.ZERO) == nfv.NEG
    assert nfv.compose_two(nfv.ZERO, nfv.ZERO) == nfv.ZERO


def test_interval_flags_irreducible_as_sampled():
    N = cfg.CfgNode
    nodes = {"n0#tool_call": N("n0", "tool_call"), "A#tool_call": N("A", "tool_call"), "B#tool_call": N("B", "tool_call")}
    edges = {("n0#tool_call", "A#tool_call", "seq"), ("n0#tool_call", "B#tool_call", "seq"),
             ("A#tool_call", "B#tool_call", "seq"), ("B#tool_call", "A#tool_call", "seq")}
    g = cfg.TraceCFG(nodes=nodes, edges=edges, entry="n0#tool_call", terminals=set())
    rec = ri.recover_interval(g, norm.normalize(g))
    assert "IRREDUCIBLE_REGION" in rec.primitives()
    assert rec.evidence_grade == "sampled"   # cannot promote to verified under irreducibility
