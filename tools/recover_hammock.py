#!/usr/bin/env python3
"""R_H — hammock pattern recovery (Tier-0) for SP-TRACE-CFR (WO-2, SPEC §4.3).

Recognizes the Π primitives present in a normalized Trace CFG and assigns each a
per-region verdict contribution. Evidence grade is `exact` (hammock: fp_profile
none). The load-bearing soundness rule is the latent-branch rule: a decision with
latent_arms >= 1 recovers to a DECISION_OBSERVED_PARTIAL region with verdict ZERO —
never IF/IF_ELSE (a single-execution decision is not evidence of a static branch).

v0.1 scope (honest): this recognizes primitives with their node spans (SEQ,
SPAWN_JOIN, WHILE, DO_WHILE, LOOP_MULTI_EXIT, IF/IF_ELSE, DECISION_OBSERVED_PARTIAL)
and reports coverage. Full bottom-up region *collapse* to a single node, and rich
IF/IF_ELSE/SWITCH disambiguation, are v0.2. Stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

POS = "POS"
ZERO = "ZERO"
VIOLATION = "VIOLATION"


@dataclass(frozen=True)
class RecoveredRegion:
    primitive: str
    nodes: frozenset
    header: str | None = None
    verdict: str = POS
    grade: str = "exact"


@dataclass
class RecoveryResult:
    regions: list = field(default_factory=list)
    covered: set = field(default_factory=set)
    uncovered: set = field(default_factory=set)
    engine: str = "hammock"
    evidence_grade: str = "exact"

    @property
    def full_recovery(self) -> bool:
        return not self.uncovered

    def primitives(self) -> list[str]:
        return [r.primitive for r in self.regions]

    def anomalies(self) -> list[str]:
        out = []
        if any(r.verdict == VIOLATION for r in self.regions):
            out.append("GOV-SC-MULTIJOIN-001")
        return out


def _adj(edges):
    preds: dict[str, list[str]] = {}
    succs: dict[str, list[tuple[str, str]]] = {}
    for u, v, l in edges:
        succs.setdefault(u, []).append((v, l))
        preds.setdefault(v, []).append(u)
    return preds, succs


def _natural_loop(u: str, v: str, preds) -> set[str]:
    """Natural loop of backedge u->v (v = header): v plus all nodes reaching u
    without passing through v."""
    loop = {v}
    if u not in loop:
        loop.add(u)
        wl = [u]
        while wl:
            x = wl.pop()
            for p in preds.get(x, []):
                if p not in loop:
                    loop.add(p)
                    wl.append(p)
    return loop


def _reach_from(start: str, succs, blocked: str) -> set[str]:
    seen, stack = {start}, [start]
    while stack:
        x = stack.pop()
        for v, _ in succs.get(x, []):
            if v == blocked or v in seen:
                continue
            seen.add(v)
            stack.append(v)
    return seen


def recover_hammock(cfg, normalized) -> RecoveryResult:
    nodes = set(cfg.nodes)
    preds, succs = _adj(cfg.edges)
    regions: list[RecoveredRegion] = []
    covered: set[str] = set()
    loop_decisions: set[str] = set()

    # ---- loops (WHILE / DO_WHILE / LOOP_MULTI_EXIT) from backedges ----
    for u, v, _l in normalized.backedges:
        loop = _natural_loop(u, v, preds)
        decs = [nid for nid in loop if cfg.nodes[nid].kind == "decision"]
        live = [d for d in decs if not cfg.nodes[d].is_latent]
        if live:
            gpos = set().union(*[cfg.nodes[d].guard_positions for d in live])
            prim = "WHILE" if "pre" in gpos else "DO_WHILE" if "post" in gpos else "LOOP_MULTI_EXIT"
            verdict = POS
            loop_decisions.update(decs)
        else:
            prim, verdict = "LOOP_MULTI_EXIT", ZERO   # latent / no live guard
        regions.append(RecoveredRegion(prim, frozenset(loop), header=v, verdict=verdict))
        covered |= loop

    # ---- SPAWN_JOIN (SESE sidechain, I-SC1) ----
    spawn_es = [(s, f) for (s, f, l) in cfg.edges if l == "spawn"]
    join_es = [(x, j) for (x, j, l) in cfg.edges if l == "join"]
    if len(spawn_es) == 1 and len(join_es) == 1:
        (s, f), (x, j) = spawn_es[0], join_es[0]
        inner = _reach_from(f, succs, blocked=j)
        region = {s, j} | inner
        regions.append(RecoveredRegion("SPAWN_JOIN", frozenset(region), header=s, verdict=POS))
        covered |= region
    elif len(join_es) > 1:
        # I-SC1 violation: a sidechain with >1 join edge
        region = {s for s, _ in spawn_es} | {j for _, j in join_es}
        regions.append(RecoveredRegion("SPAWN_JOIN", frozenset(region), verdict=VIOLATION))
        covered |= region

    # ---- branches (non-loop decisions) ----
    for nid, n in cfg.nodes.items():
        if n.kind != "decision" or nid in covered or nid in loop_decisions:
            continue
        if n.is_latent:
            regions.append(RecoveredRegion("DECISION_OBSERVED_PARTIAL", frozenset({nid}), header=nid, verdict=ZERO))
        else:
            arms = [v for v, l in succs.get(nid, []) if l.startswith("br_")]
            non_terminal_arms = [a for a in arms if cfg.nodes[a].kind != "terminal"]
            prim = "IF_ELSE" if len(set(arms)) >= 2 and len(non_terminal_arms) >= 2 else "IF"
            regions.append(RecoveredRegion(prim, frozenset({nid}), header=nid, verdict=POS))
        covered.add(nid)

    # ---- SEQ regions (from T2) ----
    for chain in normalized.seq_regions:
        regions.append(RecoveredRegion("SEQ", frozenset(chain), verdict=POS))
        covered |= set(chain)

    # a lone tool_call not folded into any construct is a trivial SEQ-of-one (recoverable, POS)
    for nid, n in cfg.nodes.items():
        if nid not in covered and n.kind == "tool_call":
            regions.append(RecoveredRegion("SEQ", frozenset({nid}), verdict=POS))
            covered.add(nid)

    # terminals are leaf exits, not a Π construct — don't count them against coverage
    covered |= {nid for nid, n in cfg.nodes.items() if n.kind == "terminal"}
    uncovered = nodes - covered
    return RecoveryResult(regions=regions, covered=covered, uncovered=uncovered)
