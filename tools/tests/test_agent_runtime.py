#!/usr/bin/env python3
"""Reference live agent runtime: execution emits control-flow events -> attested.

Run: python3 -m pytest -q tools/tests/test_agent_runtime.py
"""

from __future__ import annotations

import importlib.util
import json
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


ar = _load("agent_runtime")
br = _load("trace_cfr_reasoning_bridge")


def _fetch(state):
    # fails on attempts 1 and 2, succeeds on the 3rd -> loop length EMERGES from execution
    n = state.get("fetch_n", 0) + 1
    state["fetch_n"] = n
    return "ok" if n >= 3 else "retry"


def _retry_policy():
    def policy(state):
        if state.get("finished"):
            return ("done",)
        if state.get("phase", "body") == "body":     # DO_WHILE body
            state["phase"] = "guard"
            return ("tool", "fetch", None)
        state["phase"] = "body"                        # post-checked guard
        if state.get("last_result") == "ok":
            state["finished"] = True
            return ("branch", "retry-guard", "false", "post")
        return ("branch", "retry-guard", "true", "post")
    return policy


def _run():
    rt = ar.AgentRuntime("retry-1")
    events = rt.run_react(_retry_policy(), {"fetch": _fetch})
    return rt, events


def test_control_flow_emerges_from_execution():
    _, events = _run()
    calls = [e for e in events if e["eventType"] == "reasoning.tool.called"]
    branches = [e for e in events if e["eventType"] == "reasoning.decision.branched"]
    # tool succeeded on the 3rd attempt, so the loop ran 3 times (not authored)
    assert len(calls) == 3
    assert [b["controlFlow"]["branchTaken"] for b in branches] == ["true", "true", "false"]
    assert all(b["controlFlow"]["guardPosition"] == "post" for b in branches)
    assert events[-1]["eventType"] == "reasoning.run.completed"


def test_emitted_events_conform_to_sourceos_reasoning_event_schema():
    # if the canonical spec is checked out locally, the LIVE events must validate against it
    schema_path = os.path.expanduser("~/dev/sourceos-spec/schemas/ReasoningEvent.json")
    if not os.path.exists(schema_path):
        import pytest
        pytest.skip("sourceos-spec not checked out")
    from jsonschema.validators import Draft202012Validator as V
    validator = V(json.load(open(schema_path)))
    _, events = _run()
    for ev in events:
        assert list(validator.iter_errors(ev)) == [], ev["eventType"]


def test_truthful_narration_permits_the_live_run():
    rt, events = _run()
    seg = br.reasoning_events_to_segment(events, session_id="retry-1")
    covers = [seg["events"][0]["event_id"], seg["events"][-1]["event_id"]]
    rt.narrate("loop", "DO_WHILE", covers, raw="retried until the fetch succeeded")
    _att, report = rt.attest()
    assert report.permitted and report.gate_verdict == "PASS"


def test_lying_narration_fails_the_live_run_closed():
    rt, events = _run()
    seg = br.reasoning_events_to_segment(events, session_id="retry-1")
    covers = [seg["events"][0]["event_id"], seg["events"][-1]["event_id"]]
    rt.narrate("loop", "WHILE", covers, raw="I validated before each attempt")   # ran DO_WHILE
    _att, report = rt.attest()
    assert not report.permitted and report.gate_verdict == "FAIL"
