#!/usr/bin/env python3
"""P2 normalization conformance (SPEC §4.2): T5 backedge/irreducible + T2 compression.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_normalize.py
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


def _cfg_from(e):
    r = ing.ingest_sealed_segment(e.seal())
    assert r.ok, r.reasons
    return cfg.build_cfg(r.events)


def test_while_backedge_derived_and_reducible():
    e = em.TraceCfrEmitter("w")
    e.tool_call("head")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "false", "pre")
    e.terminal()
    n = norm.normalize(_cfg_from(e))
    # the loop back-edge is body -> guard (guard dominates body)
    assert ("body#tool_call", "guard#decision", "seq") in n.backedges
    assert n.reducible                       # a WHILE is reducible
    assert n.retreat_nondom == set()
    assert "guard#decision" in n.dominators["body#tool_call"]


def test_seq_chain_compresses():
    e = em.TraceCfrEmitter("q")
    e.tool_call("a")
    e.tool_call("b")
    e.tool_call("c")
    e.terminal()
    n = norm.normalize(_cfg_from(e))
    members = {tuple(r) for r in n.seq_regions}
    # a,b,c collapse into one maximal seq region (order preserved)
    assert any({"a#tool_call", "b#tool_call", "c#tool_call"}.issubset(set(r)) for r in n.seq_regions), n.seq_regions
    # and that region is contiguous/ordered
    for r in n.seq_regions:
        if "a#tool_call" in r:
            assert r.index("a#tool_call") < r.index("b#tool_call") < r.index("c#tool_call")


def test_branch_decision_not_compressed_into_single_region():
    # an IF: decision with two observed arms must not be swallowed with both arms
    e = em.TraceCfrEmitter("if")
    e.tool_call("pre")
    e.decision("g", "true")
    e.tool_call("then")
    e.terminal()
    e2 = em.TraceCfrEmitter("if")   # second run: the false arm (same sites)
    # simulate both arms by a single segment with both observed
    e3 = em.TraceCfrEmitter("if2")
    e3.tool_call("pre")
    e3.decision("g", "true")
    e3.tool_call("then")
    e3.decision("g", "false")
    e3.terminal()
    n = norm.normalize(_cfg_from(e3))
    # the decision g has out-degree 2, so no seq region contains it with both successors
    for r in n.seq_regions:
        assert not ({"then#tool_call", "exit#terminal"} <= set(r) and "g#decision" in r)


def test_irreducible_region_detected():
    # synthetic 2-entry cycle A<->B (no single header dominates) -> retreat_nondom
    N = cfg.CfgNode
    nodes = {
        "n0#tool_call": N("n0", "tool_call"),
        "A#tool_call": N("A", "tool_call"),
        "B#tool_call": N("B", "tool_call"),
    }
    edges = {
        ("n0#tool_call", "A#tool_call", "seq"),
        ("n0#tool_call", "B#tool_call", "seq"),
        ("A#tool_call", "B#tool_call", "seq"),
        ("B#tool_call", "A#tool_call", "seq"),
    }
    g = cfg.TraceCFG(nodes=nodes, edges=edges, entry="n0#tool_call", terminals=set())
    n = norm.normalize(g)
    assert not n.reducible
    assert n.retreat_nondom  # the irreducible cycle edges are flagged (GOV-IRRED material)


def test_normalization_version_stable_and_order_sensitive():
    v1 = norm.normalization_version()
    assert v1.startswith("N-0.1.0-") and v1 == norm.normalization_version()
    import hashlib
    import json
    reordered = list(reversed(norm.TRANSFORMS))
    other = "N-0.1.0-" + hashlib.blake2b(json.dumps(reordered, separators=(",", ":")).encode(), digest_size=8).hexdigest()
    assert other != v1  # changing transform order => new version
