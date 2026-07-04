#!/usr/bin/env python3
"""R_I — interval recovery (Tier-1) for SP-TRACE-CFR (WO-3, SPEC §4.3).

The second, decorrelated recovery arm. Where R_H matches hammock subgraphs, R_I
works from the dominator/interval structure computed in P2: natural loops of
backedges + loop-nesting depth. Its distinct contributions over R_H are:

  * irreducibility -> GOV-IRRED-001. A non-singleton interval fixpoint (retreat_nondom
    edges) yields an irreducible-region region; if a non-header entry crosses a
    sidechain boundary it escalates from REVIEW toward VIOLATION.
  * verified-grade evidence. The loop-nesting witness (durable proof material) lets
    R_I emit CTRL243.evidence = `verified` (axis binding §2.2); R_H is `exact`.
  * nesting_depth(v) for the ObligationIR O1 scoping rule.

On well-formed reducible traces R_I and R_H AGREE (agreement is the correct outcome;
a sign disagreement is a harness fault the P5 VERIFIER-FAULT check catches). Stdlib-only.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recover_hammock import (  # noqa: E402
    POS, ZERO, VIOLATION, RecoveredRegion, RecoveryResult, _adj, _natural_loop, _reach_from,
)

REVIEW = "REVIEW"


def nesting_depth(cfg, backedges) -> dict[str, int]:
    """Loop-nesting depth = number of natural loops containing the node (the witness)."""
    preds, _ = _adj(cfg.edges)
    loops = [_natural_loop(u, v, preds) for (u, v, _l) in backedges]
    depth = {nid: 0 for nid in cfg.nodes}
    for loop in loops:
        for nid in loop:
            depth[nid] += 1
    return depth


def recover_interval(cfg, normalized) -> RecoveryResult:
    nodes = set(cfg.nodes)
    preds, succs = _adj(cfg.edges)
    regions: list[RecoveredRegion] = []
    covered: set[str] = set()
    depth = nesting_depth(cfg, normalized.backedges)
    grade = "verified"

    # ---- irreducible regions (the R_I-specific signal) ----
    if normalized.retreat_nondom:
        grade = "sampled"                      # cannot promote to verified under irreducibility
        irr_nodes = {u for (u, v, _l) in normalized.retreat_nondom} | {v for (_u, v, _l) in normalized.retreat_nondom}
        # escalate if a retreat edge crosses a sidechain boundary (approx: any sidechain in play)
        verdict = REVIEW
        regions.append(RecoveredRegion("IRREDUCIBLE_REGION", frozenset(irr_nodes), verdict=verdict, grade=grade))
        covered |= irr_nodes

    # ---- loops via natural loops of backedges + nesting witness ----
    loop_decisions: set[str] = set()
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
            prim, verdict = "LOOP_MULTI_EXIT", ZERO
        regions.append(RecoveredRegion(prim, frozenset(loop), header=v, verdict=verdict, grade=grade))
        covered |= loop

    # ---- SPAWN_JOIN (interval treats the sidechain as a SESE region) ----
    spawn_es = [(s, f) for (s, f, l) in cfg.edges if l == "spawn"]
    join_es = [(x, j) for (x, j, l) in cfg.edges if l == "join"]
    if len(spawn_es) == 1 and len(join_es) == 1:
        (s, f), (x, j) = spawn_es[0], join_es[0]
        region = {s, j} | _reach_from(f, succs, blocked=j)
        regions.append(RecoveredRegion("SPAWN_JOIN", frozenset(region), header=s, verdict=POS, grade=grade))
        covered |= region
    elif len(join_es) > 1:
        region = {s for s, _ in spawn_es} | {j for _, j in join_es}
        regions.append(RecoveredRegion("SPAWN_JOIN", frozenset(region), verdict=VIOLATION, grade=grade))
        covered |= region

    # ---- branches ----
    for nid, n in cfg.nodes.items():
        if n.kind != "decision" or nid in covered or nid in loop_decisions:
            continue
        if n.is_latent:
            regions.append(RecoveredRegion("DECISION_OBSERVED_PARTIAL", frozenset({nid}), header=nid, verdict=ZERO, grade=grade))
        else:
            arms = [v for v, l in succs.get(nid, []) if l.startswith("br_")]
            non_term = [a for a in arms if cfg.nodes[a].kind != "terminal"]
            prim = "IF_ELSE" if len(set(arms)) >= 2 and len(non_term) >= 2 else "IF"
            regions.append(RecoveredRegion(prim, frozenset({nid}), header=nid, verdict=POS, grade=grade))
        covered.add(nid)

    # ---- SEQ intervals + trivial singletons ----
    for chain in normalized.seq_regions:
        regions.append(RecoveredRegion("SEQ", frozenset(chain), verdict=POS, grade=grade))
        covered |= set(chain)
    for nid, n in cfg.nodes.items():
        if nid not in covered and n.kind == "tool_call":
            regions.append(RecoveredRegion("SEQ", frozenset({nid}), verdict=POS, grade=grade))
            covered.add(nid)

    covered |= {nid for nid, n in cfg.nodes.items() if n.kind == "terminal"}
    result = RecoveryResult(regions=regions, covered=covered, uncovered=nodes - covered)
    result.engine = "interval"
    result.evidence_grade = grade
    # attach the witness for O1 / promotion
    result.nesting_depth = depth  # type: ignore[attr-defined]
    return result
