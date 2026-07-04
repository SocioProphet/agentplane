#!/usr/bin/env python3
"""Narration-fidelity runtime gate — the deployable capability, end to end.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_runtime.py
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


rt = _load("trace_cfr_runtime")


def _truthful_while_run(session="run-ok"):
    r = rt.RunRecorder(session)
    r.tool_call("head")
    g1 = r.decision("guard", "true", "pre")
    r.tool_call("body")
    r.decision("guard", "true", "pre")
    r.tool_call("body")
    g3 = r.decision("guard", "false", "pre")
    r.terminal()
    r.narrate("loop", "WHILE", covers=[g1, g3], raw="I looped while the guard held")
    return r


def test_truthful_run_is_permitted():
    rep = _truthful_while_run().finish()
    assert rep.gate_verdict == "PASS"
    assert rep.permitted
    assert rep.failure_traces == []


def test_lying_run_fails_closed():
    r = rt.RunRecorder("run-lie")
    b1 = r.tool_call("body")
    r.decision("guard", "true", "post")
    r.tool_call("body")
    g2 = r.decision("guard", "false", "post")
    r.terminal()
    # ran a post-checked DO_WHILE, but CLAIMS a pre-checked WHILE
    r.narrate("loop", "WHILE", covers=[b1, g2], raw="I validated before each iteration")
    rep = r.finish()
    assert rep.gate_verdict == "FAIL"
    assert not rep.permitted
    assert len(rep.failure_traces) == 1
    assert rep.failure_traces[0]["failure_cluster"] == "GOV-NARR-STRUCT-001"


def test_mixed_run_takes_most_cautious_verdict():
    r = rt.RunRecorder("run-mixed")
    b1 = r.tool_call("body")
    r.decision("guard", "true", "post")
    r.tool_call("body")
    g2 = r.decision("guard", "false", "post")
    r.terminal()
    r.narrate("truthful", "DO_WHILE", covers=[b1, g2])   # POS
    r.narrate("lie", "WHILE", covers=[b1, g2])           # NEG
    rep = r.finish()
    assert rep.gate_verdict == "FAIL"          # one lie poisons the run (most-cautious fold)
    assert not rep.permitted


def test_run_with_no_claims_is_permitted():
    r = rt.RunRecorder("run-silent")
    r.tool_call("a")
    r.tool_call("b")
    r.terminal()
    rep = r.finish()
    assert rep.gate_verdict == "PASS" and rep.permitted


def test_stepgates_are_signed_and_emitted_per_claim():
    rep = _truthful_while_run().finish()
    assert len(rep.stepgates) == 1
    art = rep.stepgates[0]
    assert art["verdict"] == "OK" and "signature" in art
