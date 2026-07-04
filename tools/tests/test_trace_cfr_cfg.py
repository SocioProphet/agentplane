#!/usr/bin/env python3
"""P1 CFG construction conformance (SPEC §4.1), via the real P0->P1 pipeline.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_cfg.py
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


def _cfg_from(emitter):
    r = ing.ingest_sealed_segment(emitter.seal())
    assert r.ok, r.reasons
    return cfg.build_cfg(r.events)


def test_linear_with_sidechain_shape():
    e = em.TraceCfrEmitter("s1", "a0")
    e.tool_call("read")
    e.tool_call("plan")
    with e.sidechain("delegate", "sc-1"):
        e.tool_call("sub.fetch")
    e.terminal()
    g = _cfg_from(e)

    assert g.entry == "read#tool_call"
    assert g.terminals == {"exit#terminal"}
    assert g.latent_sites() == set()
    labels = {lbl for _, _, lbl in g.edges}
    assert "spawn" in labels and "join" in labels
    # spawn and join at the same site_id did NOT collide into one node
    assert "delegate#spawn" in g.nodes and "delegate#join" in g.nodes
    assert g.entry in g.roots()


def test_single_execution_decision_is_latent():
    e = em.TraceCfrEmitter("s2")
    e.tool_call("a")
    e.decision("guard", branch_taken="true")   # observed once => one arm only
    e.tool_call("b")
    e.terminal()
    g = _cfg_from(e)
    node = g.nodes["guard#decision"]
    assert node.is_latent and node.latent_arms == 1
    assert "guard#decision" in g.latent_sites()


def test_while_loop_both_arms_not_latent_and_cycle_present():
    e = em.TraceCfrEmitter("s3")
    e.tool_call("head")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "false", "pre")
    e.terminal()
    g = _cfg_from(e)

    guard = g.nodes["guard#decision"]
    assert not guard.is_latent            # both true and false observed
    assert guard.distinct_arms == 2
    assert guard.guard_positions == {"pre"}         # WHILE (pre-check)
    assert g.nodes["body#tool_call"].exec_count == 2
    # the loop cycle: guard --br_true--> body and body --seq--> guard both present
    assert ("guard#decision", "body#tool_call", "br_true") in g.edges
    assert ("body#tool_call", "guard#decision", "seq") in g.edges


def test_do_while_guard_position_post():
    e = em.TraceCfrEmitter("s4")
    e.tool_call("body")
    e.decision("guard", "false", "post")   # DO_WHILE: body precedes guard
    e.terminal()
    g = _cfg_from(e)
    assert g.nodes["guard#decision"].guard_positions == {"post"}


def test_narration_and_annotations_are_not_nodes():
    e = em.TraceCfrEmitter("s5")
    e.tool_call("a")
    e.narration("n", ["x", "y"], {"primitive": "SEQ"})
    e.tool_call("b")
    e.terminal()
    g = _cfg_from(e)
    assert set(g.nodes) == {"a#tool_call", "b#tool_call", "exit#terminal"}
    assert all(n.kind in cfg.NODE_KINDS for n in g.nodes.values())
