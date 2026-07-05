#!/usr/bin/env python3
"""SP-ADAPT-TREE-001 (real edition): the EDGAR 10-K → fiber-fragment adapter.

Offline + deterministic: the parser runs on a compact HTML fixture, and the end-to-end check
runs on a REAL Apple 10-K fragment committed to the repo (generated once from the live filing) —
so `descend` is proven to navigate an actual SEC filing's table of contents with no network in
the test. The live fetch path (latest_10k / _get) is exercised by the CLI, not the suite.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    path = os.path.join(_HERE, os.pardir, f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ed = _load("edgar_fiber_adapter")
cg = _load("conformal_gate")
sg = _load("stopgate_artifact")
fp = _load("fiber_projection")
fr = _load("fiber_retrieval")

_MINI = os.path.join(_HERE, "fixtures", "edgar_mini_10k.htm")
_AAPL = os.path.join(_HERE, "fixtures", "edgar_aapl_10k.fragment.json")


def test_extract_items_recovers_clean_item_titles():
    with open(_MINI, encoding="utf-8") as fh:
        items = dict(ed.extract_items(fh.read()))
    assert items["1"] == "Business"
    assert items["1A"] == "Risk Factors"
    assert items["2"] == "Properties"
    assert items["7"] == "Management Discussion and Analysis"


def test_to_fragment_anchors_the_registrant_under_item_1():
    meta = {"cik": "1", "company": "Acme Corp", "accession": "acc-1",
            "filing_date": "2026-01-01", "url": "https://sec.gov/x"}
    frag = ed.to_fragment(meta, [("1", "Business"), ("1A", "Risk Factors")])
    assert frag["tenant_id"] == "edgar"
    entity = next(n for n in frag["nodes"] if n["graph_node"]["node_id"] == "entity/1")
    assert entity["evidence"]["anchor_ref"] == "https://sec.gov/x#item-1"
    # the registrant is contained by Item 1 (Business).
    assert {"class": "containment", "parent": "1/item-1", "child": "entity/1"} in frag["edges"]


def _gate():
    scores = [i / 100 for i in range(100)]
    return cg.calibrate(scores, [s <= 0.4 for s in scores], 0.10)


def test_real_apple_10k_fragment_projects_and_descend_navigates_it():
    with open(_AAPL, encoding="utf-8") as fh:
        frag = json.load(fh)
    g = fp.project(frag)
    root = g.id_map[("edgar", "320193/10-K")]
    items = fr.containment_children(g, root)
    assert len(items) >= 15  # the real filing's Part I–IV items
    titles = {g.display_of(c) for c in items}
    assert any("Risk Factors" in t for t in titles)
    assert any("Business" in t for t in titles)
    # descend the REAL table of contents to the Risk Factors section.
    leaf, status = fr.descend(g, root, fr.keyword_scorer(), _gate(), "what are the risk factors")
    assert status == "reached_leaf"
    assert "Risk Factors" in g.display_of(leaf)
    # the registrant is anchored to the real filing URL.
    entity = g.id_map[("edgar", "entity/320193")]
    assert g.anchor_of(entity).startswith("https://www.sec.gov/Archives/edgar/data/320193/")
