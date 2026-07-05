#!/usr/bin/env python3
"""ι_d — Crystal Atlas → hellgraph projection for SP-RETR-FIBER-001 (WO_FIBER_002 §4).

Projects the prophet-platform Crystal Atlas ingestion/evidence contracts (string ids)
into hellgraph-shaped atoms (u128 ids), so the composite graph H can be assembled on
the hellgraph substrate (BINDING.md §5 decision 1).

IN-LANE ONLY. This module deliberately does NOT touch ~/dev/hellgraph. It emits *views*
of the pending hellgraph atom schema — including the `edge_class` field that WO_FIBER_002
adds to `LinkAtom` (coordination-gated, SP_RETR_FIBER_001_WO2.md §0). When that schema
lands, swap these views for the real `hg_core` types; the projection logic and the
string↔u128 id-map are unchanged.

What it binds (SP_RETR_FIBER_001_BINDING.md §1 / WO2 §4):
  graph-node.v0.node_id      → NodeAtom, fresh u128 AtomId; id-map row (tenant,node_id)↔atom_id
  graph-node.v0.attributes   → ValueEnvelope key=attr:<k>
  graph-node.v0.distribution_class → carried as a SEPARATE axis (redistribution), NOT visibility
  evidence.v0.anchor_ref     → ValueEnvelope key=anchor, epistemic_mode=derived  (PageAnchor, INV-F3)
  adapter-attached confidentiality_class → ValueEnvelope.security  (WallGuard visibility, INV-F4)
  containment edge           → LinkAtom edge_class=Containment  (single-parent forest, INV-F1)
  GLEIF/FIBO cross-link      → LinkAtom edge_class=Relational

Two visibility vocabularies are kept distinct on purpose (BINDING.md §2.6):
  * confidentiality_class (WallGuard, access/consent) → security label, drives INV-F4.
  * distribution_class (Crystal Atlas, redistribution/licensing) → carried, NOT visibility.

Stdlib-only (repo zero-dependency posture). Run tests:
  python3 -m pytest -q tools/tests/test_fiber_projection.py
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

# --- edge classes (mirror the pending hg_core::EdgeClass, WO2 §2) ------------- #
EDGE_CONTAINMENT = "Containment"   # E^⊑ — single-parent, per-fiber, mereological
EDGE_RELATIONAL = "Relational"     # E_R — typed many-to-many

# --- evidence / provenance axis (SP_RETR_FIBER_001_axis_binding §2.3) --------- #
EPISTEMIC_DERIVED = "derived"      # recovered via projection, not observed as source authorship

# Claim atoms are stored as value-envelope keys `attr:claim:<var>` (§3.4.1); to_bundle emits
# them as K lines. Mirrors fiber_retrieval.CLAIM_PREFIX.
CLAIM_PREFIX = "attr:claim:"

# Crystal Atlas required fields (verified against the real schemas, BINDING.md §1).
_GRAPH_NODE_REQUIRED = ("node_id", "tenant_id", "node_kind", "display_name")
_EVIDENCE_REQUIRED = ("evidence_id", "tenant_id", "source_ref", "anchor_ref")


# --------------------------------------------------------------------------- #
# Views of the pending hellgraph atom schema (swap for hg_core when it lands).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NodeAtomView:
    atom_id: int          # u128-range; mirrors hg_core::AtomId
    type_name: str        # from graph-node.v0.node_kind


@dataclass(frozen=True)
class ValueEnvelopeView:
    subject_atom: int
    key: str              # "attr:<k>" | "anchor" | "distribution_class"
    payload: object
    epistemic_mode: str = EPISTEMIC_DERIVED
    security: object = None   # confidentiality_class (WallGuard). None = unlabelled → fail-closed downstream.


@dataclass(frozen=True)
class LinkAtomView:
    atom_id: int
    type_name: str        # "contains" for containment; FIBO property IRI for relational
    edge_class: str       # EDGE_CONTAINMENT | EDGE_RELATIONAL  (WO2 §2: first-class field)
    members: tuple        # ((role_name, target_atom_id, ordinal), ...)


@dataclass
class ProjectedGraph:
    nodes: dict = field(default_factory=dict)     # atom_id -> NodeAtomView
    links: list = field(default_factory=list)     # [LinkAtomView]
    values: list = field(default_factory=list)    # [ValueEnvelopeView]
    id_map: dict = field(default_factory=dict)     # (tenant_id, node_id) -> atom_id
    _child_parent: dict = field(default_factory=dict)  # atom_id -> parent atom_id (INV-F1 guard)

    # ---- queries used by invariants / retrieval ---- #
    def anchor_of(self, atom_id: int):
        """PageAnchor for an atom, or None. INV-F3 anchor-reachability primitive."""
        for v in self.values:
            if v.subject_atom == atom_id and v.key == "anchor":
                return v.payload
        return None

    def security_of(self, atom_id: int):
        """WallGuard confidentiality label (visibility axis, INV-F4). None = unlabelled."""
        for v in self.values:
            if v.subject_atom == atom_id and v.security is not None:
                return v.security
        return None

    def distribution_of(self, atom_id: int):
        """Crystal Atlas distribution_class (redistribution axis — NOT visibility)."""
        for v in self.values:
            if v.subject_atom == atom_id and v.key == "distribution_class":
                return v.payload
        return None

    def display_of(self, atom_id: int):
        """The node's display_name — the human-readable section/entity title a descend
        scorer (LLM or oracle) reads to pick a branch. None if absent."""
        for v in self.values:
            if v.subject_atom == atom_id and v.key == "display_name":
                return v.payload
        return None

    def relational_links(self):
        return [l for l in self.links if l.edge_class == EDGE_RELATIONAL]

    def containment_links(self):
        return [l for l in self.links if l.edge_class == EDGE_CONTAINMENT]


class ProjectionError(ValueError):
    """Raised on schema-invalid input or an INV violation at projection time."""


# --------------------------------------------------------------------------- #
# id-map: deterministic string → u128, so re-ingest is idempotent by construction.
# --------------------------------------------------------------------------- #
def atom_id_for(tenant_id: str, node_id: str) -> int:
    """Stable u128 AtomId for a Crystal Atlas node. Deterministic ⇒ idempotent re-ingest."""
    digest = hashlib.blake2b(
        b"%s\x00%s" % (tenant_id.encode("utf-8"), node_id.encode("utf-8")),
        digest_size=16,  # 128 bits
    ).digest()
    return int.from_bytes(digest, "big")


def _require(record: dict, fields: tuple, kind: str) -> None:
    missing = [f for f in fields if f not in record or record[f] in (None, "")]
    if missing:
        raise ProjectionError(f"{kind} missing required field(s): {missing}")


# --------------------------------------------------------------------------- #
# The projection ι_d.
# --------------------------------------------------------------------------- #
def project(fragment: dict, into: ProjectedGraph | None = None) -> ProjectedGraph:
    """Project one Crystal Atlas fragment into hellgraph atom-views.

    fragment = {
      "tenant_id": str,
      "nodes": [ { "graph_node": <graph-node.v0>,
                   "confidentiality_class": <wallguard label, adapter-attached, optional>,
                   "evidence": <evidence.v0, optional> } ],
      "edges": [ { "class": "containment", "parent": node_id, "child": node_id }
               | { "class": "relational", "type_name": <fibo IRI>,
                   "src": node_id, "dst": node_id } ],
    }

    Passing `into` an existing ProjectedGraph makes re-ingest idempotent: a node_id
    already in the id-map keeps its atom_id, and its value envelopes are replaced
    (deduplicated by (subject_atom, key)), never duplicated.
    """
    g = into if into is not None else ProjectedGraph()
    tenant = fragment.get("tenant_id")
    if not tenant:
        raise ProjectionError("fragment missing tenant_id")

    # ---- nodes + values ---- #
    for entry in fragment.get("nodes", []):
        gn = entry["graph_node"]
        _require(gn, _GRAPH_NODE_REQUIRED, "graph-node.v0")
        if gn["tenant_id"] != tenant:
            raise ProjectionError(
                f"node {gn['node_id']} tenant {gn['tenant_id']} != fragment tenant {tenant}"
            )
        key = (tenant, gn["node_id"])
        atom_id = g.id_map.get(key) or atom_id_for(tenant, gn["node_id"])
        g.id_map[key] = atom_id
        g.nodes[atom_id] = NodeAtomView(atom_id=atom_id, type_name=gn["node_kind"])

        confidentiality = entry.get("confidentiality_class")  # WallGuard label (access axis)
        _replace_value(g, atom_id, "display_name", gn["display_name"], security=confidentiality)
        _replace_value(g, atom_id, "distribution_class",
                       gn.get("distribution_class"), security=None)  # redistribution axis, NOT visibility
        for k, v in (gn.get("attributes") or {}).items():
            _replace_value(g, atom_id, f"attr:{k}", v, security=confidentiality)

        ev = entry.get("evidence")
        if ev is not None:
            _require(ev, _EVIDENCE_REQUIRED, "evidence.v0")
            _replace_value(g, atom_id, "anchor", ev["anchor_ref"], security=confidentiality)
            if "confidence" in ev:
                _replace_value(g, atom_id, "attr:evidence_confidence", ev["confidence"],
                               security=confidentiality)

    # ---- edges ---- #
    for e in fragment.get("edges", []):
        cls = e.get("class")
        if cls == "containment":
            pid = _atom(g, tenant, e["parent"])
            cid = _atom(g, tenant, e["child"])
            _add_containment(g, pid, cid)
        elif cls == "relational":
            sid = _atom(g, tenant, e["src"])
            did = _atom(g, tenant, e["dst"])
            _add_relational(g, e["type_name"], sid, did)
        else:
            raise ProjectionError(f"unknown edge class: {cls!r}")

    return g


def _atom(g: ProjectedGraph, tenant: str, node_id: str) -> int:
    key = (tenant, node_id)
    if key not in g.id_map:
        raise ProjectionError(f"edge references unknown node_id {node_id!r} (project its node first)")
    return g.id_map[key]


def _replace_value(g: ProjectedGraph, subject: int, key: str, payload, security) -> None:
    if payload is None:
        return
    g.values = [v for v in g.values if not (v.subject_atom == subject and v.key == key)]
    g.values.append(ValueEnvelopeView(subject_atom=subject, key=key, payload=payload,
                                      security=security))


def _link_id(edge_class: str, a: int, b: int, type_name: str) -> int:
    d = hashlib.blake2b(
        b"%s\x00%d\x00%d\x00%s" % (edge_class.encode(), a, b, type_name.encode()),
        digest_size=16,
    ).digest()
    return int.from_bytes(d, "big")


def _add_containment(g: ProjectedGraph, parent: int, child: int) -> None:
    # INV-F1: single-parent forest. A child may not have two distinct containment parents.
    existing = g._child_parent.get(child)
    if existing is not None and existing != parent:
        raise ProjectionError(
            f"INV-F1 violation: atom {child} would get a second containment parent "
            f"({existing} and {parent})"
        )
    if existing == parent:
        return  # idempotent re-ingest
    g._child_parent[child] = parent
    g.links.append(LinkAtomView(
        atom_id=_link_id(EDGE_CONTAINMENT, parent, child, "contains"),
        type_name="contains",
        edge_class=EDGE_CONTAINMENT,
        members=(("parent", parent, 0), ("child", child, 1)),
    ))


def _add_relational(g: ProjectedGraph, type_name: str, src: int, dst: int) -> None:
    lid = _link_id(EDGE_RELATIONAL, src, dst, type_name)
    if any(l.atom_id == lid for l in g.links):
        return  # idempotent re-ingest
    g.links.append(LinkAtomView(
        atom_id=lid,
        type_name=type_name,
        edge_class=EDGE_RELATIONAL,
        members=(("src", src, 0), ("dst", dst, 1)),
    ))


# --------------------------------------------------------------------------- #
# Invariant checks (project-time views of the spec invariants).
# --------------------------------------------------------------------------- #
def check_containment_forest(g: ProjectedGraph) -> None:
    """INV-F1: every atom has ≤ 1 containment parent (already enforced on insert; re-verify)."""
    seen_child = {}
    for l in g.containment_links():
        child = next(t for (r, t, o) in l.members if r == "child")
        parent = next(t for (r, t, o) in l.members if r == "parent")
        if child in seen_child and seen_child[child] != parent:
            raise ProjectionError(f"INV-F1: atom {child} has two containment parents")
        seen_child[child] = parent


def check_edge_class_purity(g: ProjectedGraph) -> None:
    """INV-F2 (projection view): every link carries exactly one known class."""
    for l in g.links:
        if l.edge_class not in (EDGE_CONTAINMENT, EDGE_RELATIONAL):
            raise ProjectionError(f"INV-F2: link {l.atom_id} has bad edge_class {l.edge_class!r}")


def unanchored_relational_endpoints(g: ProjectedGraph) -> list:
    """INV-F3: every E_R endpoint must be anchor-reachable. Returns offending atom ids."""
    bad = []
    for l in g.relational_links():
        for (_r, target, _o) in l.members:
            if g.anchor_of(target) is None and target not in bad:
                bad.append(target)
    return bad


# --------------------------------------------------------------------------- #
# Interchange: emit H in a language-neutral form the real hellgraph substrate ingests.
# --------------------------------------------------------------------------- #
def to_bundle(g: ProjectedGraph) -> str:
    """Serialize the composite graph H to a tab-delimited, node_id-keyed bundle:

        N<TAB>node_id<TAB>node_kind                        (atom)
        C<TAB>parent_node_id<TAB>child_node_id            (E^⊑, containment)
        R<TAB>rel_type<TAB>src_node_id<TAB>dst_node_id     (E_R, relational)
        A<TAB>node_id<TAB>anchor_ref                       (page anchor — provenance-of-location)
        K<TAB>node_id<TAB>claim_var<TAB>value<TAB>egrade    (claim atom — for the fiber-product verdict)

    Keyed by the stable string node_id (NOT the Python-internal u128 atom id), so the Rust
    ingest adapter (`hg_fiber::ingest_bundle`) rebuilds the SAME graph on the hellgraph
    substrate, minting its own atom ids. The parity contract: fiber_projection is the reference
    oracle, hg_fiber is the real engine, this bundle is what they must agree on. Deterministic
    (sorted) so it is a stable golden vector.

    N/C/R are structure and live in the real hellgraph graph. A/K are fiber-retrieval DOMAIN
    data (page anchors, ownership claims) — hellgraph's ValuePayload models only Field/Proof,
    not arbitrary strings/scalars, so on the Rust side these ride an `hg_fiber` sidecar next to
    the store (they are not core graph facts). That sidecar is what lets the fiber-product
    verdict + double grounding run on the substrate, not just in Python.
    """
    rev = {atom_id: node_id for (_tenant, node_id), atom_id in g.id_map.items()}
    nodes = [f"N\t{rev[a]}\t{g.nodes[a].type_name}" for a in sorted(g.nodes, key=lambda a: rev[a])]
    cont, rel, anchors, claims = [], [], [], []
    for l in g.containment_links():
        p = next(t for (r, t, _o) in l.members if r == "parent")
        c = next(t for (r, t, _o) in l.members if r == "child")
        cont.append(f"C\t{rev[p]}\t{rev[c]}")
    for l in g.relational_links():
        s = next(t for (r, t, _o) in l.members if r == "src")
        d = next(t for (r, t, _o) in l.members if r == "dst")
        rel.append(f"R\t{l.type_name}\t{rev[s]}\t{rev[d]}")
    for v in g.values:
        node_id = rev[v.subject_atom]
        if v.key == "anchor":
            anchors.append(f"A\t{node_id}\t{v.payload}")
        elif v.key.startswith(CLAIM_PREFIX):
            var = v.key[len(CLAIM_PREFIX):]
            claims.append(f"K\t{node_id}\t{var}\t{v.payload['value']}\t{v.payload['egrade']}")
    return "\n".join(nodes + sorted(cont) + sorted(rel) + sorted(anchors) + sorted(claims)) + "\n"
