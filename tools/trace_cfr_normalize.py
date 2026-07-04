#!/usr/bin/env python3
"""P2 — Normalization N = [T1..T5] for SP-TRACE-CFR (WO-1, SPEC §4.2).

Applied in order to a Trace CFG (tools/trace_cfr_cfg.py). The blake2b of the
canonical transform list IS the `normalization_version`; changing the order is a
new version. The two load-bearing transforms for recovery are implemented in full:

  * T5 backedge derivation — dominators (iterative dataflow); an edge (u->v) is a
    natural-loop `backedge` iff v dominates u. Cycle edges that are NOT dominated
    (v reaches u but does not dominate it) are `retreat_nondom` — the raw material
    of GOV-IRRED-001 (irreducible regions). This is what lets R_H match WHILE/DO_WHILE.
  * T2 seq-chain compression — maximal runs of `seq` edges whose interior nodes are
    in-deg-1/out-deg-1 collapse into a SEQ region (member list retained). Backedges
    are excluded so loops are not compressed across the header.

T1 (empty-node elision), T3 (short-circuit fold), T4 (jump-thread flag-only) are
included in the ordered pipeline with conservative v0.1 behavior (documented on
each). Stdlib-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

# ordered transform list; its canonical hash is the normalization_version
TRANSFORMS = ["T1-empty@0.1", "T2-seq@0.1", "T3-shortcircuit@0.1", "T4-thread@0.1", "T5-backedge@0.1"]


def normalization_version() -> str:
    canon = json.dumps(TRANSFORMS, separators=(",", ":")).encode("utf-8")
    return "N-0.1.0-" + hashlib.blake2b(canon, digest_size=8).hexdigest()


@dataclass
class NormalizedCFG:
    dominators: dict[str, set[str]]
    backedges: set[tuple[str, str, str]]
    retreat_nondom: set[tuple[str, str, str]]
    seq_regions: list[list[str]]
    threaded_suspect: set[str] = field(default_factory=set)
    normalization_version: str = ""

    @property
    def reducible(self) -> bool:
        return not self.retreat_nondom


def _preds_succs(nodes, edges):
    preds = {n: [] for n in nodes}
    succs = {n: [] for n in nodes}
    for u, v, l in edges:
        succs[u].append((v, l))
        preds[v].append((u, l))
    return preds, succs


def dominators(nodes: set[str], edges: set, entry: str) -> dict[str, set[str]]:
    """Iterative dominator dataflow: dom(n) = {n} U (intersection of dom over preds)."""
    preds, _ = _preds_succs(nodes, edges)
    alln = set(nodes)
    dom = {n: set(alln) for n in nodes}
    dom[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for n in nodes:
            if n == entry:
                continue
            ps = [p for p, _ in preds[n]]
            if ps:
                inter = set(alln)
                for p in ps:
                    inter &= dom[p]
                new = {n} | inter
            else:
                new = {n}  # unreachable from entry -> dominates only itself
            if new != dom[n]:
                dom[n] = new
                changed = True
    return dom


def retreating_edges(nodes, edges, entry) -> set[tuple[str, str, str]]:
    """DFS back-edges: (u->v) is retreating iff v is gray (an ancestor on the DFS
    stack) when u->v is traversed. Forward edges into a loop body are NOT retreating."""
    succs = {n: [] for n in nodes}
    for u, v, l in edges:
        succs[u].append((v, l))
    color = {n: 0 for n in nodes}   # 0 white, 1 gray, 2 black
    retreating: set[tuple[str, str, str]] = set()

    def visit(u):
        color[u] = 1
        for v, l in succs[u]:
            if color[v] == 1:
                retreating.add((u, v, l))
            elif color[v] == 0:
                visit(v)
        color[u] = 2

    visit(entry)
    for n in nodes:  # any node unreachable from entry (should not occur in a trace)
        if color[n] == 0:
            visit(n)
    return retreating


def classify_edges(nodes, edges, entry):
    """T5: among retreating edges, natural-loop backedge iff v dominates u; the rest
    (v does not dominate u) are irreducible retreat_nondom (GOV-IRRED material)."""
    dom = dominators(nodes, edges, entry)
    retreating = retreating_edges(nodes, edges, entry)
    backedges = {(u, v, l) for (u, v, l) in retreating if v in dom[u]}
    retreat = retreating - backedges
    return dom, backedges, retreat


def compress_seq(nodes, edges, backedges) -> list[list[str]]:
    """T2: maximal seq chains (interior in1/out1) -> SEQ regions. Excludes backedges."""
    out_all, in_all = {}, {}
    for u, v, l in edges:
        if (u, v, l) in backedges:
            continue
        out_all.setdefault(u, []).append((v, l))
        in_all.setdefault(v, []).append((u, l))
    nxt: dict[str, str] = {}
    for u, v, l in edges:
        if (u, v, l) in backedges or l != "seq":
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


def normalize(cfg) -> NormalizedCFG:
    """Run N = [T1..T5] to produce the normalized view R_H/R_I consume."""
    nodes, edges, entry = set(cfg.nodes), set(cfg.edges), cfg.entry
    # T1 empty-node elision: v0.1 conservative no-op (our trace nodes carry tool effect;
    # no non-effectful pass-throughs are emitted). Mechanism reserved.
    # T5 first computes backedges so T2 does not compress across a loop header.
    dom, backedges, retreat = classify_edges(nodes, edges, entry)
    # T2 chain compression.
    seq_regions = compress_seq(nodes, edges, backedges)
    # T3 short-circuit fold: detect-only in v0.1 (no canonical a&&b/a||b shape is
    # synthesized here); T4 jump-thread: flag-only, none flagged on well-formed traces.
    threaded: set[str] = set()
    return NormalizedCFG(
        dominators=dom,
        backedges=backedges,
        retreat_nondom=retreat,
        seq_regions=seq_regions,
        threaded_suspect=threaded,
        normalization_version=normalization_version(),
    )
