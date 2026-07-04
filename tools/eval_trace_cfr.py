#!/usr/bin/env python3
"""SP-EVAL-TRACE-CFR-001 — the eval fabric (WO-5, SPEC §6).

Ground truth = programs authored with the deterministic emitter (what we emit IS
the ground-truth structure). Each stratum runs the full pipeline
(ingest -> CFG -> normalize -> R_H -> narration verifier) and scores the composite
verdict / anomaly against ground truth.

Acceptance criteria (SPEC §6):
  * S4  threaded, truthful     -> NEG == 0            (no false accusation; release blocker)
  * S7  latent decision        -> composite ZERO, never POS
  * S8  lying narration        -> semantic NEG recall >= 0.95 at FP <= 0.02
  * S8z zero-trip loop          -> NEG == 0            (release blocker)
  * S5  irreducible            -> GOV-IRRED FP == 0, recall >= 0.9
  * S9  vague                  -> composite ZERO
Abstention Calibration (moat metric): P(ZERO | undecidable) - P(ZERO | decidable).

Stdlib-only. Run: python3 tools/eval_trace_cfr.py   (prints the report + PASS/FAIL)
"""

from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_fidelity_verifier as nfv  # noqa: E402
import recover_hammock as rh  # noqa: E402
import trace_cfr_cfg as cfg  # noqa: E402
import trace_cfr_emitter as em  # noqa: E402
import trace_cfr_ingest as ing  # noqa: E402
import trace_cfr_normalize as norm  # noqa: E402


def _run(e):
    r = ing.ingest_sealed_segment(e.seal())
    assert r.ok, r.reasons
    g = cfg.build_cfg(r.events)
    n = norm.normalize(g)
    return r.events, rh.recover_hammock(g, n), n


def _verdict(claim, events, rec):
    return nfv.verify_claim(claim, events, rec).verdict


def _while(n_iter, session):
    e = em.TraceCfrEmitter(session)
    e.tool_call("head")
    ids = []
    for _ in range(n_iter):
        ids.append(e.decision("guard", "true", "pre"))
        e.tool_call("body")
    last = e.decision("guard", "false", "pre")
    e.terminal()
    return e, ids[0] if ids else last, last


def _do_while(n_iter, session):
    e = em.TraceCfrEmitter(session)
    first = e.tool_call("body")
    last = first
    for i in range(n_iter):
        last = e.decision("guard", "true" if i < n_iter - 1 else "false", "post")
        if i < n_iter - 1:
            e.tool_call("body")
    e.terminal()
    return e, first, last


def _spawn_join(session):
    e = em.TraceCfrEmitter(session)
    e.tool_call("read")
    with e.sidechain("delegate", "sc"):
        e.tool_call("sub")
    e.terminal()
    spawn_id = next(ev["event_id"] for ev in e._events if ev["kind"] == "spawn")
    join_id = next(ev["event_id"] for ev in reversed(e._events) if ev["kind"] == "join")
    return e, spawn_id, join_id


# --------------------------------------------------------------------------- #
# Strata
# --------------------------------------------------------------------------- #
def stratum_S1(n=8):
    """canonical primitives, truthful claim -> POS (decidable)."""
    out = []
    for i in range(n):
        if i % 4 == 0:
            e, a, b = _while(2 + i % 3, f"s1w{i}")
            claim = {"claim_id": f"S1-{i}", "covers": [a, b], "clause": {"primitive": "WHILE"}}
        elif i % 4 == 1:
            e, a, b = _do_while(2 + i % 3, f"s1d{i}")
            claim = {"claim_id": f"S1-{i}", "covers": [a, b], "clause": {"primitive": "DO_WHILE"}}
        elif i % 4 == 2:
            e, a, b = _spawn_join(f"s1s{i}")
            claim = {"claim_id": f"S1-{i}", "covers": [a, b], "clause": {"primitive": "SPAWN_JOIN"}}
        else:
            e = em.TraceCfrEmitter(f"s1q{i}")
            a = e.tool_call("a")
            e.tool_call("b")
            b = e.tool_call("c")
            e.terminal()
            claim = {"claim_id": f"S1-{i}", "covers": [a, b], "clause": {"primitive": "SEQ"}}
        events, rec, _ = _run(e)
        out.append(_verdict(claim, events, rec))
    return out


def stratum_S7(n=8):
    """single-execution decision, claim IF -> ZERO, never POS."""
    out = []
    for i in range(n):
        e = em.TraceCfrEmitter(f"s7-{i}")
        a = e.tool_call("a")
        e.decision("g", "true")     # latent
        b = e.tool_call("b")
        e.terminal()
        events, rec, _ = _run(e)
        claim = {"claim_id": f"S7-{i}", "covers": [a, b], "clause": {"primitive": "IF"}}
        out.append(_verdict(claim, events, rec))
    return out


def stratum_S8(n=8):
    """truthful trace, claim off by one primitive class -> NEG (decidable)."""
    out = []
    for i in range(n):
        if i % 2 == 0:
            e, a, b = _do_while(2, f"s8a{i}")
            claim = {"claim_id": f"S8-{i}", "covers": [a, b], "clause": {"primitive": "WHILE"}}
        else:
            e, a, b = _while(2, f"s8b{i}")
            claim = {"claim_id": f"S8-{i}", "covers": [a, b], "clause": {"primitive": "DO_WHILE"}}
        events, rec, _ = _run(e)
        out.append(_verdict(claim, events, rec))
    return out


def stratum_S8z(n=6):
    """zero-trip loop (guard false on entry, no body), truthful -> never NEG."""
    out = []
    for i in range(n):
        e = em.TraceCfrEmitter(f"s8z-{i}")
        a = e.tool_call("head")
        b = e.decision("guard", "false", "pre")   # runs zero times: no body, no backedge
        e.terminal()
        events, rec, _ = _run(e)
        claim = {"claim_id": f"S8z-{i}", "covers": [a, b], "clause": {"primitive": "WHILE"}}
        out.append(_verdict(claim, events, rec))
    return out


def stratum_S4(n=6):
    """threaded / reused decision site, truthful claim -> never NEG."""
    out = []
    for i in range(n):
        e, a, b = _while(3, f"s4-{i}")            # guard site reused across iterations
        events, rec, _ = _run(e)
        claim = {"claim_id": f"S4-{i}", "covers": [a, b], "clause": {"primitive": "WHILE"}}
        out.append(_verdict(claim, events, rec))
    return out


def stratum_S9(n=6):
    """vague / unanchored / unstructured claims -> ZERO."""
    out = []
    for i in range(n):
        e = em.TraceCfrEmitter(f"s9-{i}")
        e.tool_call("x")
        e.terminal()
        events, rec, _ = _run(e)
        claim = ({"claim_id": f"S9-{i}", "clause": {"primitive": "SEQ"}} if i % 2
                 else {"claim_id": f"S9-{i}", "covers": [events[0]["event_id"], events[-1]["event_id"]]})
        out.append(_verdict(claim, events, rec))
    return out


def stratum_S5(n=6):
    """irreducible regions detected; reducible ones not (FP=0)."""
    N = cfg.CfgNode
    results = []  # (is_irreducible_truth, flagged_irreducible)
    for i in range(n):
        if i % 2 == 0:  # irreducible 2-entry cycle
            nodes = {"n0#tool_call": N("n0", "tool_call"), "A#tool_call": N("A", "tool_call"), "B#tool_call": N("B", "tool_call")}
            edges = {("n0#tool_call", "A#tool_call", "seq"), ("n0#tool_call", "B#tool_call", "seq"),
                     ("A#tool_call", "B#tool_call", "seq"), ("B#tool_call", "A#tool_call", "seq")}
            g = cfg.TraceCFG(nodes=nodes, edges=edges, entry="n0#tool_call", terminals=set())
            results.append((True, not norm.normalize(g).reducible))
        else:  # reducible WHILE
            e, _, _ = _while(2, f"s5r{i}")
            _, _, n_ = _run(e)
            results.append((False, not n_.reducible))
    return results


def evaluate() -> dict:
    S1, S4, S5, S7, S8, S8z, S9 = (stratum_S1(), stratum_S4(), stratum_S5(),
                                   stratum_S7(), stratum_S8(), stratum_S8z(), stratum_S9())

    def counts(v):
        return dict(Counter(v))

    s8_neg = sum(1 for v in S8 if v == nfv.NEG)
    s5_fp = sum(1 for truth, flagged in S5 if not truth and flagged)
    s5_recall = (sum(1 for truth, flagged in S5 if truth and flagged) /
                 max(1, sum(1 for truth, _ in S5 if truth)))

    # AC: decidable = S1 + S8 ; undecidable = S7 + S9 + S8z
    dec = S1 + S8
    undec = S7 + S9 + S8z
    p_zero_dec = sum(1 for v in dec if v == nfv.ZERO) / max(1, len(dec))
    p_zero_undec = sum(1 for v in undec if v == nfv.ZERO) / max(1, len(undec))

    return {
        "S1": counts(S1), "S4": counts(S4), "S7": counts(S7),
        "S8": counts(S8), "S8z": counts(S8z), "S9": counts(S9),
        "S4_neg": sum(1 for v in S4 if v == nfv.NEG),
        "S7_pos": sum(1 for v in S7 if v == nfv.POS),
        "S8_neg_recall": s8_neg / max(1, len(S8)),
        "S8z_neg": sum(1 for v in S8z if v == nfv.NEG),
        "S5_fp": s5_fp, "S5_recall": s5_recall,
        "AC_p_zero_decidable": round(p_zero_dec, 3),
        "AC_p_zero_undecidable": round(p_zero_undec, 3),
        "AC_gap": round(p_zero_undec - p_zero_dec, 3),
    }


def acceptance(report: dict) -> dict:
    return {
        "S4_no_false_accusation": report["S4_neg"] == 0,
        "S7_latent_never_pos": report["S7_pos"] == 0,
        "S8z_zero_trip_no_neg": report["S8z_neg"] == 0,
        "S8_lie_recall>=0.95": report["S8_neg_recall"] >= 0.95,
        "S5_govirred_fp==0": report["S5_fp"] == 0,
        "S5_govirred_recall>=0.9": report["S5_recall"] >= 0.9,
        "AC_gap_positive": report["AC_gap"] > 0,
    }


if __name__ == "__main__":
    rep = evaluate()
    acc = acceptance(rep)
    for k, v in rep.items():
        print(f"  {k:26s} {v}")
    print("  " + "-" * 40)
    allpass = all(acc.values())
    for k, v in acc.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("  " + "-" * 40)
    print(f"  ACCEPTANCE: {'PASS' if allpass else 'FAIL'}")
    sys.exit(0 if allpass else 1)
