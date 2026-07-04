#!/usr/bin/env python3
"""WO-0.A conformance: reference emitter produces schema-valid, deterministically
sealed segments that satisfy the P0 ingest invariants by construction.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_emitter.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

from jsonschema.validators import Draft202012Validator as V

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.join(_HERE, os.pardir)
_SCHEMA = os.path.join(_TOOLS, os.pardir, "schemas", "trace-cfr-segment.schema.v0.1.json")

_spec = importlib.util.spec_from_file_location("trace_cfr_emitter", os.path.join(_TOOLS, "trace_cfr_emitter.py"))
em = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = em
_spec.loader.exec_module(em)

_VALIDATOR = V(json.load(open(_SCHEMA)))


def _build_linear_with_sidechain(session="s1"):
    e = em.TraceCfrEmitter(session_id=session, agent_id="a0")
    e.tool_call("site.read")
    e.tool_call("site.plan")
    with e.sidechain("site.delegate", "sc-1"):
        e.tool_call("site.sub.fetch")
        e.tool_call("site.sub.summarize")
    e.terminal()
    return e


def test_segment_is_schema_valid():
    seg = _build_linear_with_sidechain().seal(log_uri="mem://seg/1")
    errors = list(_VALIDATOR.iter_errors(seg))
    assert errors == [], errors[0].message if errors else ""


def test_sealing_is_deterministic():
    a = _build_linear_with_sidechain("sX").seal()
    b = _build_linear_with_sidechain("sX").seal()
    assert a["segment"]["segment_hash"] == b["segment"]["segment_hash"]
    assert a == b


def test_p0_ingest_invariants_hold_by_construction():
    seg = _build_linear_with_sidechain().seal()
    events = seg["events"]
    # monotone strictly-increasing ts within the agent
    ts = [e["ts_mono_ns"] for e in events]
    assert all(ts[i] < ts[i + 1] for i in range(len(ts) - 1))
    # unique event ids
    ids = [e["event_id"] for e in events]
    assert len(ids) == len(set(ids))
    # no dangling parent: every parent_event_id is None or an earlier event
    seen: set[str] = set()
    for e in events:
        p = e["parent_event_id"]
        assert p is None or p in seen, f"dangling parent {p}"
        seen.add(e["event_id"])
    # segment refs point at real first/last events
    assert seg["segment"]["first_event_id"] == events[0]["event_id"]
    assert seg["segment"]["last_event_id"] == events[-1]["event_id"]


def test_sidechain_is_sese_and_inner_tagged():
    seg = _build_linear_with_sidechain().seal()
    assert em.sidechain_sese_ok(seg)
    inner = [e for e in seg["events"] if e.get("sidechain_id") == "sc-1"]
    assert len(inner) == 2 and all(e["kind"] == "tool_call" for e in inner)
    # exactly one spawn and one join bracket it
    assert sum(1 for e in seg["events"] if e["kind"] == "spawn") == 1
    assert sum(1 for e in seg["events"] if e["kind"] == "join") == 1


def test_decision_guard_position_recorded():
    e = em.TraceCfrEmitter("sD")
    e.decision("loop.a", branch_taken="true", guard_position="pre")   # WHILE
    e.tool_call("body")
    e.decision("loop.b", branch_taken="false", guard_position="post")  # DO_WHILE
    seg = e.seal()
    decs = [ev for ev in seg["events"] if ev["kind"] == "decision"]
    assert [d["guard_position"] for d in decs] == ["pre", "post"]
    assert list(_VALIDATOR.iter_errors(seg)) == []
