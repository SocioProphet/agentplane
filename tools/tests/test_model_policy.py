#!/usr/bin/env python3
"""ModelPolicy: a Claude model drives the runtime; its narration is gated.

Uses a scripted fake Anthropic client (no live API) to prove the wiring end to end —
swapping in `anthropic.Anthropic()` makes it a live model agent with zero other changes.

Run: python3 -m pytest -q tools/tests/test_model_policy.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import SimpleNamespace

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, _TOOLS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ar = _load("agent_runtime")
mp = _load("model_policy")


# --- scripted fake Anthropic client (matches the SDK surface ModelPolicy uses) --- #
class _FakeMessages:
    def __init__(self, tool_uses):
        self._responses = iter(
            SimpleNamespace(content=[SimpleNamespace(type="tool_use", name=n, input=i, id=f"tu{k}")])
            for k, (n, i) in enumerate(tool_uses)
        )

    def create(self, **_kwargs):
        return next(self._responses)


def _fake_client(tool_uses):
    return SimpleNamespace(messages=_FakeMessages(tool_uses))


# the model "decides" a post-checked retry loop that runs the body twice
_POLICY_SCRIPT = [
    ("call_tool", {"tool": "body"}),
    ("loop_guard", {"site": "guard", "continue_loop": True, "position": "post"}),
    ("call_tool", {"tool": "body"}),
    ("loop_guard", {"site": "guard", "continue_loop": False, "position": "post"}),
    ("finish", {}),
]


def _run_model_agent(session):
    rt = ar.AgentRuntime(session)
    policy = mp.ModelPolicy(_fake_client(_POLICY_SCRIPT))
    events = rt.run_react(policy, {"body": lambda s: "ok"})
    return rt, events


def test_model_drives_control_flow_via_tool_use():
    _, events = _run_model_agent("m1")
    assert sum(1 for e in events if e["eventType"] == "reasoning.tool.called") == 2
    branches = [e for e in events if e["eventType"] == "reasoning.decision.branched"]
    assert [b["controlFlow"]["branchTaken"] for b in branches] == ["true", "false"]
    assert all(b["controlFlow"]["guardPosition"] == "post" for b in branches)
    assert events[-1]["eventType"] == "reasoning.run.completed"


def test_truthful_model_narration_permits():
    rt, events = _run_model_agent("m2")
    claim = mp.narrate_claim(_fake_client([("narrate", {"primitive": "DO_WHILE"})]), events, session_id="m2")
    rt.claims.append(claim)
    _att, report = rt.attest()
    assert report.permitted and report.gate_verdict == "PASS"


def test_model_misreporting_its_control_flow_fails_closed():
    rt, events = _run_model_agent("m3")
    # the model ran a post-checked DO_WHILE but claims a pre-checked WHILE
    claim = mp.narrate_claim(_fake_client([("narrate", {"primitive": "WHILE"})]), events, session_id="m3")
    rt.claims.append(claim)
    _att, report = rt.attest()
    assert not report.permitted and report.gate_verdict == "FAIL"
    assert report.failure_traces[0]["failure_cluster"] == "GOV-NARR-STRUCT-001"


def test_action_mapping():
    assert mp.ModelPolicy._to_action("call_tool", {"tool": "read", "arg": "x"}) == ("tool", "read", "x")
    assert mp.ModelPolicy._to_action("loop_guard", {"site": "g", "continue_loop": False, "position": "pre"}) == ("branch", "g", "false", "pre")
    assert mp.ModelPolicy._to_action("finish", {}) == ("done",)
