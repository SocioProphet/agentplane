#!/usr/bin/env python3
"""Fibered retrieval algebra over the composite graph H (SP-RETR-FIBER-001, WO_FIBER_005-007).

Option A — prove the descend/traverse/verdict loop against an in-memory H (built by
fiber_projection) BEFORE any Rust ingestion plumbing. If the algebra doesn't earn its keep
on the fixture, we saved ourselves the plumbing.

The four moving parts, each bound to a real mechanism where one exists:
  * traverse : one E_R hop between fibers — deterministic base router, WallGuard-filtered,
               beam-capped. Follows ONLY relational edges (INV-F2 / F4 / F10).
  * descend  : an E^⊑ walk within one fiber toward a page-anchored leaf, using the REAL
               conformal abstention gate (conformal_gate.py, CRC) to decide advance vs
               abstain. Follows ONLY containment edges (INV-F2 / F5).
  * glue_verdict : the cross-fiber fiber-product verdict POS/ZERO/NEG over shared claim
               variables (§3.3 / §3.4, INV-F6), with the forced-ZERO extraction floor.
  * retrieve_edge : run a guarded word over {traverse, descend} and assemble a DOUBLY
               grounded result — page anchors (location) + verdict & grade (claim) — §6.3.

Verdict values are the real narration enum (POS/ZERO/NEG/INDETERMINATE,
narration_fidelity_verifier.py:33). A conformal abstention yields INDETERMINATE, kept
distinct from ZERO in the trace, per SP_RETR_FIBER_001_axis_binding §2.1. Evidence grade is
{exact, sampled, verified} (axis-binding §2.2), NOT a numeric E-scale.

NOT yet done here (WO_FIBER_007): signing the result as a StopGate artifact. retrieve_edge
assembles the Episode fields; sealing them is the next step. Stdlib + the real conformal_gate.

Run:  python3 -m pytest -q tools/tests/test_fiber_retrieval.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conformal_gate as cg  # noqa: E402  (real CRC abstention gate)
import fiber_projection as fp  # noqa: E402  (the ι_d projection: builds H)

# Verdict axis — mirror narration_fidelity_verifier.py:33 (do not invent a new enum).
POS, ZERO, NEG, INDETERMINATE = "POS", "ZERO", "NEG", "INDETERMINATE"

# Evidence-grade axis — CTRL243.evidence (axis-binding §2.2). Rank for the E_floor / min.
_GRADE_RANK = {"sampled": 0, "verified": 1, "exact": 2}

# Claim atoms live in the value-envelope namespace attr:claim:<var> (§3.4.1). Each payload is
# {"value": <canonical measure>, "egrade": <grade>} — two filings that both assert the same
# canonical (predicate, arg) slot share a claim variable.
CLAIM_PREFIX = "attr:claim:"


class RetrievalError(ValueError):
    pass


# --------------------------------------------------------------------------- #
# H accessors over a ProjectedGraph (fiber_projection.ProjectedGraph).
# --------------------------------------------------------------------------- #
def containment_children(g, node):
    """E^⊑ children of `node`, within its fiber. descend walks these and ONLY these."""
    out = []
    for l in g.containment_links():
        parent = next(t for (r, t, _o) in l.members if r == "parent")
        child = next(t for (r, t, _o) in l.members if r == "child")
        if parent == node:
            out.append(child)
    return sorted(out)


def relational_neighbors(g, node, rel_type):
    """E_R neighbours of `node` along `rel_type`. traverse follows these and ONLY these."""
    out = []
    for l in g.relational_links():
        if l.type_name != rel_type:
            continue
        src = next(t for (r, t, _o) in l.members if r == "src")
        dst = next(t for (r, t, _o) in l.members if r == "dst")
        if src == node:
            out.append(dst)
    return out


def allow_all(_g, _node):
    return True


def label_gate(cleared):
    """WallGuard-style visibility (INV-F4), fail-closed: a node is visible only if its
    confidentiality label is present AND cleared. Unlabelled or uncleared ⇒ hidden."""
    cleared = set(cleared)

    def visible(g, node):
        sec = g.security_of(node)
        return sec is not None and sec in cleared

    return visible


# --------------------------------------------------------------------------- #
# The two operators.
# --------------------------------------------------------------------------- #
def traverse(g, frontier, rel_type, beam_k, visible=allow_all):
    """One E_R hop. Deterministic given H + the (deterministic) ordering; WallGuard-filtered
    (INV-F4); beam-capped to k (INV-F10). Never crosses E^⊑ (INV-F2)."""
    nxt = []
    for v in frontier:
        for w in relational_neighbors(g, v, rel_type):
            if visible(g, w):
                nxt.append(w)
    uniq = sorted(set(nxt))  # deterministic; a real beam would rank by relevance
    return uniq[:beam_k]


def descend(g, start, scorer, gate, query):
    """Root→leaf E^⊑ walk within one fiber. At each internal node the scorer gives a
    nonconformity score per child (HIGH = more likely wrong); the REAL conformal gate accepts
    the best child or abstains. Returns (leaf_atom | None, verdict) where verdict is
    INDETERMINATE on abstention (INV-F5) — never a guessed child. Only follows E^⊑ (INV-F2)."""
    node = start
    while True:
        children = containment_children(g, node)
        if not children:
            return node, "reached_leaf"  # ⊑-monotone terminated at a leaf
        scores = scorer(g, node, children, query)
        best = min(children, key=lambda c: scores[c])
        if gate.classify(scores[best]) == cg.ACCEPT:
            node = best
        else:
            return None, INDETERMINATE  # abstain: ambiguous branch, no confident citation


# --------------------------------------------------------------------------- #
# Fiber-product verdict (§3.3 / §3.4).
# --------------------------------------------------------------------------- #
def _claims(g, atom_id):
    out = {}
    for v in g.values:
        if v.subject_atom == atom_id and v.key.startswith(CLAIM_PREFIX):
            out[v.key[len(CLAIM_PREFIX):]] = v.payload  # {"value":..., "egrade":...}
    return out


def shared_claim_vars(g, a, b):
    return set(_claims(g, a)) & set(_claims(g, b))


def _restrict(g, atom_id, overlap, e_floor):
    """Project claims onto `overlap`; return {var: (value, egrade)} or None if any claim in
    the overlap is below E_floor (the forced-ZERO floor, §3.4.3)."""
    floor = _GRADE_RANK[e_floor]
    claims = _claims(g, atom_id)
    proj = {}
    for var in overlap:
        atom = claims.get(var)
        if atom is None:
            return None
        grade = atom.get("egrade", "sampled")
        if _GRADE_RANK.get(grade, -1) < floor:
            return None  # extraction below the floor ⇒ no test possible
        proj[var] = (atom["value"], grade)
    return proj


def _compatible(x, y, tol):
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        return abs(x - y) <= tol
    return x == y


def _min_grade(ra, rb):
    grades = [g for (_v, g) in list(ra.values()) + list(rb.values())]
    return min(grades, key=lambda g: _GRADE_RANK[g])


def glue_verdict(g, a, b, e_floor="sampled", tol=0.0):
    """The cross-fiber verdict as the status of the constraint fiber product (INV-F6).
    Returns (verdict, witness | None, egrade). POS/NEG carry a witness; ZERO may not."""
    overlap = shared_claim_vars(g, a, b)
    if not overlap:
        return ZERO, None, "NA"  # vacuous cover: no shared variable, no test possible
    ra = _restrict(g, a, overlap, e_floor)
    rb = _restrict(g, b, overlap, e_floor)
    if ra is None or rb is None:
        return ZERO, None, "NA"  # forced-ZERO floor / missing evidence
    disagree = [
        (var, ra[var][0], rb[var][0])
        for var in overlap
        if not _compatible(ra[var][0], rb[var][0], tol)
    ]
    egrade = _min_grade(ra, rb)
    if disagree:
        return NEG, {"disagree": disagree}, egrade  # obstruction: sections provably disagree
    agree = [(var, ra[var][0]) for var in overlap]
    return POS, {"agree": agree}, egrade  # a global section glues


# --------------------------------------------------------------------------- #
# End-to-end: a guarded word + double grounding (§6.3 / §6.4).
# --------------------------------------------------------------------------- #
@dataclass
class RetrievalResult:
    verdict: str
    egrade: str
    citations: list = field(default_factory=list)  # provenance-of-location (page anchors)
    witness: object = None                          # provenance-of-claim
    answer: object = None                           # the reached entity (or None)
    trace: list = field(default_factory=list)       # hop log for the Episode
    episode: dict = field(default_factory=dict)     # Artifact/Claim/Test/Attestation/Narrative

    @property
    def doubly_grounded(self):
        """§6.3: a real answer carries BOTH a page anchor AND a non-ZERO verdict."""
        return (
            self.verdict in (POS, NEG)
            and len(self.citations) >= 2
            and all(self.citations)
        )


def retrieve_edge(g, start, rel_type, *, scorer, gate, query,
                  beam_k=8, e_floor="sampled", tol=0.0, visible=allow_all):
    """Run `traverse rel_type ; descend` from `start`, then verdict the crossed edge and
    double-ground it. This is the ownership-DAG plan: cross a fiber boundary, locate both
    endpoints to their page anchors, and test cross-document consistency."""
    trace = [("start", start)]

    # base move: cross to the other fiber (deterministic router)
    frontier = traverse(g, [start], rel_type, beam_k, visible=visible)
    trace.append(("traverse", rel_type, list(frontier)))
    if not frontier:
        return RetrievalResult(verdict=ZERO, egrade="NA", trace=trace,
                               episode={"Test": "no relational neighbour visible"})
    target = frontier[0]

    # fiber moves: locate each endpoint to its anchored leaf (descend within its fiber)
    src_leaf, src_status = descend(g, _fiber_root(g, start), scorer, gate, query)
    dst_leaf, dst_status = descend(g, _fiber_root(g, target), scorer, gate, query)
    trace.append(("descend", {"src": src_status, "dst": dst_status}))
    if INDETERMINATE in (src_status, dst_status):
        # abstained before reaching a leaf ⇒ endpoint unanchored ⇒ whole path INDETERMINATE
        return RetrievalResult(verdict=INDETERMINATE, egrade="NA", answer=target, trace=trace,
                               episode={"Test": "conformal abstention during descent"})

    # verdict + double grounding
    verdict, witness, egrade = glue_verdict(g, start, target, e_floor=e_floor, tol=tol)
    citations = [g.anchor_of(src_leaf), g.anchor_of(dst_leaf)]
    trace.append(("verdict", verdict, egrade))
    episode = {
        "Artifact": citations,                 # tree leaves / page anchors
        "Claim": (rel_type, start, target),    # the relational edge
        "Test": "cross-fiber fiber-product over shared claim variables",
        "Attestation": "UNSIGNED (WO_FIBER_007: seal as StopGate artifact)",
        "Narrative": f"{start} -{rel_type}-> {target}: {verdict} ({egrade})",
    }
    return RetrievalResult(verdict=verdict, egrade=egrade, citations=citations,
                           witness=witness, answer=target, trace=trace, episode=episode)


def _fiber_root(g, node):
    """Climb E^⊑ to the fiber root (the document root of `node`)."""
    cur = node
    seen = set()
    while cur not in seen:
        seen.add(cur)
        parent = None
        for l in g.containment_links():
            child = next(t for (r, t, _o) in l.members if r == "child")
            if child == cur:
                parent = next(t for (r, t, _o) in l.members if r == "parent")
                break
        if parent is None:
            return cur
        cur = parent
    return cur


# --------------------------------------------------------------------------- #
# Helpers for callers/tests: build a CRC gate, and a fixture scorer.
# --------------------------------------------------------------------------- #
def calibrate_gate(scores, correct, alpha=0.10):
    """Thin pass-through to the real split-CRC calibration."""
    return cg.calibrate(scores, correct, alpha)


def scored_walk(score_by_node, default=1.0):
    """A scorer that returns a fixed nonconformity per candidate child (fixture/oracle stand-in
    for the LLM branch selector). HIGH score = more likely wrong ⇒ pushes toward abstention.
    `default` is the score for children not in the map (low ⇒ confident, high ⇒ abstain)."""
    def scorer(_g, _node, children, _query):
        return {c: score_by_node.get(c, default) for c in children}
    return scorer
