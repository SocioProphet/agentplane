#!/usr/bin/env python3
"""P2 — Normalization N = [T1..T5] for SP-TRACE-CFR (WO-1, SPEC §4.2).

Applied in order to a Trace CFG (tools/trace_cfr_cfg.py). The blake2b of the
canonical transform list IS the `normalization_version`; changing the order is a
new version. The two load-bearing transforms for recovery are implemented in full:

  * T5 backedge derivation — Cooper-Harvey-Kennedy immediate dominators (near-linear,
    no full dom-sets) + iterative DFS retreating-edge detection. An edge (u->v) is a
    natural-loop `backedge` iff v dominates u; retreating edges that are NOT dominated
    are `retreat_nondom` — the raw material of GOV-IRRED-001 (irreducible regions).
  * T2 seq-chain compression — maximal `seq` runs of straight-line nodes collapse into
    a SEQ region; backedges and control-flow nodes are excluded.

Both dominators and DFS are ITERATIVE so a 2,000-node linear segment neither blows
the Tier-0 latency budget nor Python's recursion limit. T1 (empty-node elision),
T3 (short-circuit fold), T4 (jump-thread flag-only) are conservative v0.1. Stdlib-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

TRANSFORMS = ["T1-empty@0.1", "T2-seq@0.1", "T3-shortcircuit@0.1", "T4-thread@0.1", "T5-backedge@0.1"]


def normalization_version() -> str:
    canon = json.dumps(TRANSFORMS, separators=(",", ":")).encode("utf-8")
    return "N-0.1.0-" + hashlib.blake2b(canon, digest_size=8).hexdigest()


def _preds_succs(nodes, edges):
    preds = {n: [] for n in nodes}
    succs = {n: [] for n in nodes}
    for u, v, l in edges:
        succs[u].append((v, l))
        preds[v].append((u, l))
    return preds, succs


def _postorder(nodes, succs, entry) -> list[str]:
    """Iterative DFS postorder (entry last). Unreached nodes appended after."""
    visited = {entry}
    order: list[str] = []
    stack = [(entry, iter(succs.get(entry, [])))]
    while stack:
        node, it = stack[-1]
        advanced = False
        for v, _l in it:
            if v not in visited:
                visited.add(v)
                stack.append((v, iter(succs.get(v, []))))
                advanced = True
                break
        if not advanced:
            order.append(node)
            stack.pop()
    for n in nodes:
        if n not in visited:
            order.append(n)
    return order


def compute_idom(nodes, edges, entry) -> dict[str, str]:
    """Cooper-Harvey-Kennedy immediate dominators (postorder-numbered fingers)."""
    preds, succs = _preds_succs(nodes, edges)
    post = _postorder(nodes, succs, entry)
    pnum = {n: i for i, n in enumerate(post)}   # entry has the highest number
    idom: dict[str, str] = {entry: entry}

    def intersect(a: str, b: str) -> str:
        while a != b:
            while pnum[a] < pnum[b]:
                a = idom[a]
            while pnum[b] < pnum[a]:
                b = idom[b]
        return a

    changed = True
    while changed:
        changed = False
        for b in reversed(post):            # reverse postorder, entry first
            if b == entry:
                continue
            new_idom = None
            for p, _l in preds[b]:
                if p in idom:
                    new_idom = p if new_idom is None else intersect(p, new_idom)
            if new_idom is not None and idom.get(b) != new_idom:
                idom[b] = new_idom
                changed = True
    return idom


def _dominates(v: str, u: str, idom: dict[str, str]) -> bool:
    """True iff v is on u's immediate-dominator chain (v dominates u)."""
    x = u
    while True:
        if x == v:
            return True
        nxt = idom.get(x)
        if nxt is None or nxt == x:
            return False
        x = nxt


def retreating_edges(nodes, edges, entry) -> set[tuple[str, str, str]]:
    """Iterative-DFS back-edges: (u->v) retreating iff v is gray (an ancestor on the
    DFS stack) when u->v is traversed. Forward edges into a loop body are NOT retreating."""
    _, succs = _preds_succs(nodes, edges)
    color = {n: 0 for n in nodes}   # 0 white, 1 gray, 2 black
    retreating: set[tuple[str, str, str]] = set()

    def dfs(start):
        color[start] = 1
        stack = [(start, iter(succs.get(start, [])))]
        while stack:
            node, it = stack[-1]
            advanced = False
            for v, l in it:
                if color[v] == 1:
                    retreating.add((node, v, l))
                elif color[v] == 0:
                    color[v] = 1
                    stack.append((v, iter(succs.get(v, []))))
                    advanced = True
                    break
            if not advanced:
                color[node] = 2
                stack.pop()

    dfs(entry)
    for n in nodes:
        if color[n] == 0:
            dfs(n)
    return retreating


def classify_edges(nodes, edges, entry):
    """T5: among retreating edges, natural-loop backedge iff v dominates u; the rest
    are irreducible retreat_nondom (GOV-IRRED material)."""
    idom = compute_idom(nodes, edges, entry)
    retreating = retreating_edges(nodes, edges, entry)
    backedges = {(u, v, l) for (u, v, l) in retreating if _dominates(v, u, idom)}
    retreat = retreating - backedges
    return idom, backedges, retreat


def compress_seq(nodes, edges, backedges, linear: set | None = None) -> list[list[str]]:
    """T2: maximal seq chains (interior in1/out1) -> SEQ regions. Excludes backedges.

    `linear` restricts compression to straight-line nodes (tool_call/terminal); a
    control-flow node (decision/spawn/join) is never absorbed into a SEQ region,
    so e.g. a latent decision stays visible to the latent-branch rule in R_H."""
    if linear is None:
        linear = set(nodes)
    out_all, in_all = {}, {}
    for u, v, l in edges:
        if (u, v, l) in backedges:
            continue
        out_all.setdefault(u, []).append((v, l))
        in_all.setdefault(v, []).append((u, l))
    nxt: dict[str, str] = {}
    for u, v, l in edges:
        if (u, v, l) in backedges or l != "seq" or u not in linear or v not in linear:
            continue
        if out_all.get(u) == [(v, "seq")] and in_all.get(v) == [(u, "seq")]:
            nxt[u] = v
    targets = set(nxt.values())
    regions = []
    for start in nxt:
        if start in targets:
            continue
        chain, cur = [start], start
        while cur in nxt:
            cur = nxt[cur]
            chain.append(cur)
        if len(chain) > 1:
            regions.append(chain)
    return regions


@dataclass
class NormalizedCFG:
    idom: dict[str, str]
    backedges: set[tuple[str, str, str]]
    retreat_nondom: set[tuple[str, str, str]]
    seq_regions: list[list[str]]
    threaded_suspect: set[str] = field(default_factory=set)
    normalization_version: str = ""

    @property
    def reducible(self) -> bool:
        return not self.retreat_nondom

    def dominates(self, v: str, u: str) -> bool:
        return _dominates(v, u, self.idom)

    @property
    def dominators(self) -> dict[str, set[str]]:
        """Lazily materialize full dominator sets from idom (diagnostics/tests only —
        NOT used on the Tier-0 hot path)."""
        out: dict[str, set[str]] = {}
        for n in self.idom:
            s, x = set(), n
            while True:
                s.add(x)
                nx = self.idom.get(x)
                if nx is None or nx == x:
                    break
                x = nx
            out[n] = s
        return out


def normalize(cfg) -> NormalizedCFG:
    """Run N = [T1..T5] to produce the normalized view R_H/R_I consume."""
    nodes, edges, entry = set(cfg.nodes), set(cfg.edges), cfg.entry
    idom, backedges, retreat = classify_edges(nodes, edges, entry)
    linear = {nid for nid, n in cfg.nodes.items() if n.kind in ("tool_call", "terminal")}
    seq_regions = compress_seq(nodes, edges, backedges, linear)
    return NormalizedCFG(
        idom=idom,
        backedges=backedges,
        retreat_nondom=retreat,
        seq_regions=seq_regions,
        threaded_suspect=set(),
        normalization_version=normalization_version(),
    )
