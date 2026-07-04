#!/usr/bin/env python3
"""R_H hammock recovery conformance (SPEC §4.3), full pipeline.

Run: python3 -m pytest -q tools/tests/test_recover_hammock.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)


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


def _recover(e):
    r = ing.ingest_sealed_segment(e.seal())
    assert r.ok, r.reasons
    g = cfg.build_cfg(r.events)
    return rh.recover_hammock(g, norm.normalize(g))


def test_seq_and_spawn_join_full_recovery():
    e = em.TraceCfrEmitter("s1")
    e.tool_call("read")
    e.tool_call("plan")
    with e.sidechain("delegate", "sc-1"):
        e.tool_call("sub.fetch")
    e.terminal()
    res = _recover(e)
    assert "SPAWN_JOIN" in res.primitives()
    assert "SEQ" in res.primitives()
    assert res.evidence_grade == "exact"
    assert res.full_recovery, res.uncovered


def test_while_recovered():
    e = em.TraceCfrEmitter("w")
    e.tool_call("head")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "false", "pre")
    e.terminal()
    res = _recover(e)
    assert "WHILE" in res.primitives()
    while_region = next(r for r in res.regions if r.primitive == "WHILE")
    assert while_region.verdict == "POS" and while_region.grade == "exact"


def test_do_while_recovered():
    e = em.TraceCfrEmitter("d")
    e.tool_call("body")
    e.decision("guard", "true", "post")
    e.tool_call("body")
    e.decision("guard", "false", "post")
    e.terminal()
    res = _recover(e)
    assert "DO_WHILE" in res.primitives()
    assert "WHILE" not in res.primitives()   # pre != post


def test_latent_decision_is_zero_never_if():
    # single-execution decision => latent => DECISION_OBSERVED_PARTIAL/ZERO, NOT IF
    e = em.TraceCfrEmitter("if")
    e.tool_call("a")
    e.decision("g", "true")   # observed once
    e.tool_call("b")
    e.terminal()
    res = _recover(e)
    assert "IF" not in res.primitives() and "IF_ELSE" not in res.primitives()
    partial = next(r for r in res.regions if r.primitive == "DECISION_OBSERVED_PARTIAL")
    assert partial.verdict == "ZERO"
    assert "g#decision" in partial.nodes


def test_evidence_grade_is_exact_for_hammock():
    e = em.TraceCfrEmitter("g")
    e.tool_call("only")
    e.terminal()
    res = _recover(e)
    assert res.engine == "hammock" and res.evidence_grade == "exact"
