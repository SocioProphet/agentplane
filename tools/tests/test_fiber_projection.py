#!/usr/bin/env python3
"""WO_FIBER_002 §5 acceptance for the ι_d Crystal Atlas → hellgraph projection.

Proves, without touching ~/dev/hellgraph:
  * a known GLEIF Level-2 ownership chain reconstructs across two fibers;
  * every E_R endpoint is anchor-reachable (INV-F3);
  * containment is a single-parent forest and a double-parent insert is rejected (INV-F1);
  * every link carries exactly one edge_class (INV-F2, projection view);
  * WallGuard confidentiality_class rides the security axis and is NOT the same as
    Crystal Atlas distribution_class (BINDING.md §2.6);
  * re-ingest is idempotent — no atom or edge duplication (WO2 §4 id-map contract).

Stdlib + pytest. Run: python3 -m pytest -q tools/tests/test_fiber_projection.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_MOD = os.path.join(_HERE, os.pardir, "fiber_projection.py")
_spec = importlib.util.spec_from_file_location("fiber_projection", _MOD)
fp = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = fp
_spec.loader.exec_module(fp)

_FIXTURE = os.path.join(_HERE, "fixtures", "fiber_ownership_dag.json")


def _load():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _atom(g, node_id):
    return g.id_map[("acme-tenant", node_id)]


# --------------------------------------------------------------------------- #
def test_ownership_chain_reconstructs_across_two_fibers():
    g = fp.project(_load())
    parent = _atom(g, "entity/parentco")
    sub = _atom(g, "entity/subco")
    rels = g.relational_links()
    assert len(rels) == 1
    (link,) = rels
    assert link.type_name == "gleif-L2:isDirectParentOf"
    assert link.edge_class == fp.EDGE_RELATIONAL
    src = next(t for (r, t, o) in link.members if r == "src")
    dst = next(t for (r, t, o) in link.members if r == "dst")
    assert (src, dst) == (parent, sub)
    # the two entities live in DIFFERENT fibers (different filing roots) — the whole point.
    assert _atom(g, "filing-A/root") != _atom(g, "filing-B/root")


def test_inv_f3_endpoints_anchor_reachable():
    g = fp.project(_load())
    assert fp.unanchored_relational_endpoints(g) == []
    # anchors are the real evidence.v0 anchor_refs, per fiber.
    assert g.anchor_of(_atom(g, "entity/parentco")) == "filing-A#p87§4.2"
    assert g.anchor_of(_atom(g, "entity/subco")) == "filing-B#p14§2.1"


def test_inv_f1_containment_is_single_parent_forest():
    g = fp.project(_load())
    fp.check_containment_forest(g)  # no raise
    # 4 containment edges, each child has exactly one parent.
    children = [next(t for (r, t, o) in l.members if r == "child") for l in g.containment_links()]
    assert len(children) == len(set(children)) == 4


def test_inv_f1_rejects_second_containment_parent():
    frag = _load()
    frag["edges"].append(
        {"class": "containment", "parent": "filing-B/root", "child": "entity/parentco"}
    )
    with pytest.raises(fp.ProjectionError, match="INV-F1"):
        fp.project(frag)


def test_inv_f2_every_link_has_one_known_class():
    g = fp.project(_load())
    fp.check_edge_class_purity(g)  # no raise
    classes = {l.edge_class for l in g.links}
    assert classes == {fp.EDGE_CONTAINMENT, fp.EDGE_RELATIONAL}


def test_two_visibility_vocabularies_are_distinct():
    g = fp.project(_load())
    parent = _atom(g, "entity/parentco")
    sub = _atom(g, "entity/subco")
    # confidentiality_class (WallGuard, access) rides the security axis...
    assert g.security_of(parent) == "firm_approved"
    assert g.security_of(sub) == "matter_restricted"
    # ...distribution_class (redistribution) is carried on a SEPARATE axis, not as security.
    assert g.distribution_of(parent) == "public_derived"
    assert g.distribution_of(sub) == "internal_private"
    assert g.security_of(sub) != g.distribution_of(sub)


def test_reingest_is_idempotent():
    frag = _load()
    g = fp.project(frag)
    n_nodes, n_links, n_values = len(g.nodes), len(g.links), len(g.values)
    ids_before = dict(g.id_map)
    # project the same fragment again into the same graph.
    fp.project(frag, into=g)
    assert len(g.nodes) == n_nodes
    assert len(g.links) == n_links
    assert len(g.values) == n_values      # values replaced, not appended
    assert g.id_map == ids_before          # atom ids stable


def test_atom_id_is_deterministic_u128():
    a = fp.atom_id_for("acme-tenant", "entity/parentco")
    b = fp.atom_id_for("acme-tenant", "entity/parentco")
    assert a == b
    assert 0 <= a < (1 << 128)
    # different node → different id (with overwhelming probability).
    assert a != fp.atom_id_for("acme-tenant", "entity/subco")


def test_schema_invalid_node_rejected():
    frag = _load()
    del frag["nodes"][0]["graph_node"]["node_kind"]
    with pytest.raises(fp.ProjectionError, match="graph-node.v0 missing"):
        fp.project(frag)


def test_edge_referencing_unknown_node_rejected():
    frag = {"tenant_id": "acme-tenant", "nodes": [],
            "edges": [{"class": "relational", "type_name": "x",
                       "src": "ghost/a", "dst": "ghost/b"}]}
    with pytest.raises(fp.ProjectionError, match="unknown node_id"):
        fp.project(frag)


def test_to_bundle_matches_golden_parity_vector():
    # The bundle is the contract the Rust hg_fiber ingest must reproduce byte-for-byte.
    g = fp.project(_load())
    b = fp.to_bundle(g)
    with open(os.path.join(_HERE, "fixtures", "fiber_ownership.bundle"), encoding="utf-8") as fh:
        assert b == fh.read()
    # structure — keyed by node_id (not the internal u128 atom id) so a different engine rebuilds H.
    assert "N\tentity/parentco\torganization" in b
    assert "R\tgleif-L2:isDirectParentOf\tentity/parentco\tentity/subco" in b
    # domain data for double-grounding on the substrate: anchors (A) + claims (K).
    assert "A\tentity/parentco\tfiling-A#p87§4.2" in b
    assert "K\tentity/parentco\towns_pct:parentco|subco\t100\tverified" in b
    assert "K\tentity/subco\towns_pct:parentco|subco\t100\tverified" in b
