#!/usr/bin/env python3
"""Bridge: ReasoningEvents -> trace-cfr segment -> narration verdict, end to end.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_reasoning_bridge.py
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


br = _load("trace_cfr_reasoning_bridge")
rt = _load("trace_cfr_runtime")
sg = _load("stopgate_artifact")
ing = _load("trace_cfr_ingest")


def _ev(eid, etype, trust="trusted-control-input", trace="workspace-safe", **cf):
    e = {"id": eid, "type": "ReasoningEvent", "specVersion": "2.0.0", "runRef": "urn:srcos:reasoning-run:t",
         "eventType": etype, "summary": "", "traceLevel": trace, "trustLevel": trust, "capturedAt": "2026-07-04T00:00:00Z"}
    if cf:
        e["controlFlow"] = cf
    return e


def _dowhile_events():
    # a run that executed a post-checked DO_WHILE loop, expressed as ReasoningEvents
    return [
        _ev("e0", "reasoning.run.created"),                                  # skipped (not control-flow)
        _ev("e1", "reasoning.tool.called", site="body"),
        _ev("e2", "reasoning.decision.branched", site="guard", branch_taken="true", guard_position="post"),
        _ev("e3", "reasoning.tool.called", site="body"),
        _ev("e4", "reasoning.decision.branched", site="guard", branch_taken="false", guard_position="post"),
        _ev("e5", "reasoning.run.completed", site="exit"),
    ]


def test_bridge_projects_events_to_valid_ingestible_segment():
    seg = br.reasoning_events_to_segment(_dowhile_events(), session_id="t")
    r = ing.ingest_sealed_segment(seg)
    assert r.ok, r.reasons
    assert seg["segment"]["log_uri"].startswith("reasoning://")


def test_truthful_reasoning_run_permits():
    events = _dowhile_events()
    seg = br.reasoning_events_to_segment(events, session_id="t")
    # find the loop span event ids -> their node covers
    claims = [{"claim_id": "loop", "covers": [seg["events"][0]["event_id"], seg["events"][-1]["event_id"]],
               "clause": {"primitive": "DO_WHILE"}}]
    rep = rt.gate_segment(seg, claims, sg.Signer.from_seed(b"\x03" * 32, "k"))
    assert rep.gate_verdict == "PASS" and rep.permitted


def test_lying_reasoning_run_fails_closed():
    seg = br.reasoning_events_to_segment(_dowhile_events(), session_id="t")
    # agent CLAIMS a pre-checked WHILE but the events show a post-checked DO_WHILE
    claims = [{"claim_id": "loop", "covers": [seg["events"][0]["event_id"], seg["events"][-1]["event_id"]],
               "clause": {"primitive": "WHILE"}}]
    rep = rt.gate_segment(seg, claims, sg.Signer.from_seed(b"\x03" * 32, "k"))
    assert rep.gate_verdict == "FAIL" and not rep.permitted


def test_trustlevel_maps_to_taint_and_gates_exfiltration():
    # a recipient argument derived from an untrusted observation must be denied
    assert br.taint_label("trusted-control-input") == "TRUSTED"
    assert br.taint_label("untrusted-observation") == "UNTRUSTED"
    events = [
        _ev("a1", "reasoning.tool.called", trust="untrusted-observation", arg="recipient"),
    ]
    finding, viols = br.taint_gate_from_events(events, required={"recipient": "TRUSTED"})
    assert finding == "VIOLATION"
    assert viols[0].arg_name == "recipient" and viols[0].actual == "UNTRUSTED"


def test_non_controlflow_events_alone_raise():
    import pytest
    with pytest.raises(ValueError):
        br.reasoning_events_to_segment([_ev("e0", "reasoning.run.created")])
