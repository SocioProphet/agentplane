#!/usr/bin/env python3
"""P1 — Trace CFG construction for SP-TRACE-CFR (WO-1, SPEC §4.1).

Builds the control-flow graph T = (V, E, entry, X) from a SEALED segment
(tools/trace_cfr_ingest.py output). Key rules from §4.1:

  * Nodes are events with kind in {tool_call, decision, spawn, join, terminal};
    narration / tool_result / gate are annotations, not nodes.
  * Repeated executions of the same site fold into one node. Node key is
    (site_id, kind): the §4.1 site fold, plus `kind` so a spawn and a join that
    happen to share a site_id do not collide.
  * Edge label comes from the SOURCE event: a decision contributes br_<taken>,
    a spawn contributes `spawn`, a return from a sidechain to a join contributes
    `join`, everything else `seq`.
  * LATENT BRANCH: a decision node with fewer than two distinct observed taken
    labels (i.e. only one out-edge across the segment) has latent_arms >= 1.
    Recovery MUST NOT conclude SEQ from such a node (dynamic trace != static CFG).
  * guard_position (pre/post) is retained per decision for the WHILE vs DO_WHILE
    distinction (§4.4).

Backedge derivation and normalization are P2 (SPEC §4.2), NOT done here: loop
cycles appear as coincident forward edges; classifying the backedge is deferred.
Stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

NODE_KINDS = {"tool_call", "decision", "spawn", "join", "terminal"}


@dataclass
class CfgNode:
    site_id: str
    kind: str
    exec_count: int = 0
    taken_labels: list[str] = field(default_factory=list)   # decisions only
    guard_positions: set[str] = field(default_factory=set)
    event_ids: list[str] = field(default_factory=list)

    @property
    def node_id(self) -> str:
        return f"{self.site_id}#{self.kind}"

    @property
    def distinct_arms(self) -> int:
        return len(set(self.taken_labels))

    @property
    def latent_arms(self) -> int:
        """>=1 iff a decision was observed taking fewer than two distinct arms."""
        if self.kind != "decision":
            return 0
        return 1 if self.distinct_arms < 2 else 0

    @property
    def is_latent(self) -> bool:
        return self.latent_arms > 0


@dataclass
class TraceCFG:
    nodes: dict[str, CfgNode]
    edges: set[tuple[str, str, str]]      # (from_node_id, to_node_id, label)
    entry: str | None
    terminals: set[str]

    def roots(self) -> set[str]:
        """Nodes with no incoming edge (diagnostic; entry should be among them)."""
        has_in = {dst for _, dst, _ in self.edges}
        return set(self.nodes) - has_in

    def latent_sites(self) -> set[str]:
        return {nid for nid, n in self.nodes.items() if n.is_latent}


def _edge_label(src: dict, dst: dict) -> str:
    if src["kind"] == "decision":
        return "br_" + (src.get("branch_taken") or "unknown")
    if src["kind"] == "spawn":
        return "spawn"
    if dst["kind"] == "join" and src.get("sidechain_id"):
        return "join"
    return "seq"


def build_cfg(events: list[dict]) -> TraceCFG:
    """Construct the Trace CFG from ordered (sealed) segment events."""
    node_events = [e for e in events if e["kind"] in NODE_KINDS]
    if not node_events:
        return TraceCFG(nodes={}, edges=set(), entry=None, terminals=set())

    nodes: dict[str, CfgNode] = {}

    def _node(ev: dict) -> CfgNode:
        nid = f"{ev['site_id']}#{ev['kind']}"
        n = nodes.get(nid)
        if n is None:
            n = CfgNode(site_id=ev["site_id"], kind=ev["kind"])
            nodes[nid] = n
        n.exec_count += 1
        n.event_ids.append(ev["event_id"])
        if ev["kind"] == "decision":
            n.taken_labels.append(ev.get("branch_taken") or "unknown")
            if ev.get("guard_position"):
                n.guard_positions.add(ev["guard_position"])
        return n

    # first pass: materialize nodes (fold)
    for ev in node_events:
        _node(ev)

    # second pass: edges between consecutive node-events
    edges: set[tuple[str, str, str]] = set()
    for src, dst in zip(node_events, node_events[1:]):
        s_id = f"{src['site_id']}#{src['kind']}"
        d_id = f"{dst['site_id']}#{dst['kind']}"
        edges.add((s_id, d_id, _edge_label(src, dst)))

    entry = f"{node_events[0]['site_id']}#{node_events[0]['kind']}"
    terminals = {nid for nid, n in nodes.items() if n.kind == "terminal"}
    return TraceCFG(nodes=nodes, edges=edges, entry=entry, terminals=terminals)
