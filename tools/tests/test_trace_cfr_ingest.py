#!/usr/bin/env python3
"""P0 ingest conformance (SPEC §4.0): seal round-trip + no-repair rejection.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_ingest.py
"""

from __future__ import annotations

import importlib.util
import json
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


def _seg_bytes(session="s1"):
    e = em.TraceCfrEmitter(session, "a0")
    e.tool_call("read")
    e.tool_call("plan")
    with e.sidechain("delegate", "sc-1"):
        e.tool_call("sub.fetch")
    e.terminal()
    return e


def test_emitter_output_ingests_as_sealed():
    e = _seg_bytes()
    raw = e.to_jsonl()
    sealed = e.seal()
    r = ing.ingest(raw, expected_hash=sealed["segment"]["segment_hash"])
    assert r.ok, r.reasons
    assert r.segment_hash == sealed["segment"]["segment_hash"]
    assert len(r.events) == len(e._events)


def test_sealed_segment_roundtrip():
    r = ing.ingest_sealed_segment(_seg_bytes().seal())
    assert r.ok, r.reasons


def test_seal_mismatch_detected():
    raw = _seg_bytes().to_jsonl()
    r = ing.ingest(raw, expected_hash="sha256:" + "0" * 64)
    assert not r.ok and any("SEAL_MISMATCH" in x for x in r.reasons)


def test_non_monotone_ts_rejected_no_repair():
    e = _seg_bytes()
    seg = e.seal()
    seg["events"][2]["ts_mono_ns"] = 0  # break monotonicity mid-stream
    r = ing.ingest_sealed_segment(seg)
    assert not r.ok
    assert any("NON_MONOTONE_TS" in x for x in r.reasons)
    assert r.events == []  # no repair: nothing returned


def test_missing_site_id_rejected():
    e = _seg_bytes()
    seg = e.seal()
    del seg["events"][0]["site_id"]
    r = ing.ingest_sealed_segment(seg)
    assert not r.ok and any("MISSING_FIELD" in x for x in r.reasons)


def test_duplicate_event_id_rejected():
    e = _seg_bytes()
    seg = e.seal()
    seg["events"][1]["event_id"] = seg["events"][0]["event_id"]
    r = ing.ingest_sealed_segment(seg)
    assert not r.ok and any("DUPLICATE_EVENT_ID" in x for x in r.reasons)


def test_dangling_parent_rejected():
    e = _seg_bytes()
    seg = e.seal()
    seg["events"][2]["parent_event_id"] = "ghost:999999"
    r = ing.ingest_sealed_segment(seg)
    assert not r.ok and any("DANGLING_PARENT" in x for x in r.reasons)


def test_malformed_json_rejected():
    raw = _seg_bytes().to_jsonl() + b'{"event_id": broken}\n'
    r = ing.ingest(raw)
    assert not r.ok and any("MALFORMED_JSON" in x for x in r.reasons)
