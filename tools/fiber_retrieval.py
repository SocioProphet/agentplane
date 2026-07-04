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
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conformal_gate as cg  # noqa: E402  (real CRC abstention gate)
import fiber_projection as fp  # noqa: E402  (the ι_d projection: builds H)
import stopgate_artifact as sg  # noqa: E402  (real ed25519 StopGate sealing)

# Verdict axis — mirror narration_fidelity_verifier.py:33 (do not invent a new enum).
POS, ZERO, NEG, INDETERMINATE = "POS", "ZERO", "NEG", "INDETERMINATE"

# Verdict → VerifierIR finding (axis-binding §2.1; mirrors narration_fidelity_verifier.py:36).
# StopGate then maps finding → PASS/FAIL/INDETERMINATE. Only POS is permit-eligible; ZERO and
# a conformal abstention are both no-permit (finding None), kept distinct only in the trace.
_VERDICT_TO_FINDING = {
    POS: sg.FINDING_OK,
    NEG: sg.FINDING_VIOLATION,
    ZERO: sg.FINDING_NONE,
    INDETERMINATE: sg.FINDING_NONE,
}

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


# --------------------------------------------------------------------------- #
# WO_FIBER_007 — seal the Episode as a signed StopGate artifact (§6.4).
# --------------------------------------------------------------------------- #
def seal_episode(result, *, signer, session_id, workcell_id,
                 window_start, window_end, evaluated_at=None,
                 gate_id="fiber-retrieval", lift_authority="michael-only", keyring=None):
    """Seal a RetrievalResult's Episode as a signed StopGate artifact.

    The HARNESS (not the model) evaluates: our verdict → VerifierIR finding → StopGate
    PASS/FAIL/INDETERMINATE, ed25519-signed. The page anchors become the artifact's
    semantic-layer evidence, so a POS is layer-bound (§5.3); the Episode fields + native
    verdict + grade + witness ride in `extra`. Returns (signed_artifact, disposition).
    Only a POS carrying anchors seals to PASS (permit) — everything else is no-permit.
    """
    finding = _VERDICT_TO_FINDING[result.verdict]
    evidence = [
        sg.Evidence(
            source_event_uuid=str(cite),
            evidence_hash=sg.sha256_evidence(str(cite)),
            layer="semantic",
            mode="presence",
        )
        for cite in result.citations
        if cite
    ]
    raw = sg.FINDING_TO_VERDICT[finding]
    verdict, notes = sg.degrade_verdict(raw, evidence, "semantic", None, keyring)
    unsigned = sg.build_unsigned(
        gate_id=gate_id,
        session_id=session_id,
        workcell_id=workcell_id,
        subject=[str(result.answer)] if result.answer is not None else [],
        predicate="fibered-retrieval:cross-fiber-consistency",
        verdict=verdict,
        evidence=evidence,
        evaluated_by={"component": "fiber_retrieval.seal_episode",
                      "version": "0.1.0", "kind": sg.HARNESS_KIND},
        evaluated_at=evaluated_at or sg.utc_now_iso(),
        window_start=window_start,
        window_end=window_end,
        lift_authority=lift_authority,
        predicate_layer="semantic",
        extra={
            "fiber_episode": result.episode,
            "native_verdict": result.verdict,  # POS/ZERO/NEG/INDETERMINATE (pre-StopGate)
            "evidence_grade": result.egrade,    # exact / sampled / verified
            "witness": result.witness,
            "degrade_notes": notes,
        },
    )
    signed = sg.sign_artifact(unsigned, signer)
    return signed, sg.DISPOSITION[verdict]


# --------------------------------------------------------------------------- #
# Branch scorers for descend. The scorer is the ONE swappable seam: the algebra,
# the conformal gate, and the sealing are identical whether the branch decision
# comes from a lexical heuristic or a frontier model.
# --------------------------------------------------------------------------- #
def _words(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def keyword_scorer():
    """A deterministic, dependency-free navigator: nonconformity = low for the child whose
    title UNIQUELY best-overlaps the query, high for the rest. Ties or no-overlap push every
    child high, so the conformal gate abstains rather than guess. The honest floor beneath
    llm_scorer — it navigates real branches with no model and no network."""

    def scorer(g, _node, children, query):
        q = _words(query)
        overlap = {c: len(q & _words(g.display_of(c))) for c in children}
        best = max(overlap.values()) if overlap else 0
        if best == 0 or list(overlap.values()).count(best) > 1:
            return {c: 1.0 for c in children}  # no clear winner → abstain
        return {c: (0.1 if overlap[c] == best else 0.9) for c in children}

    return scorer


# ---- live model-backed scorer (turns the oracle into real reasoning) ---- #
MODEL = "claude-opus-4-8"  # matches model_policy.MODEL; adaptive thinking on

RANK_TOOL = {
    "name": "rank_child_section",
    "description": (
        "Given a query and candidate child sections (by index + title), pick the single child "
        "most likely to contain the answer. If none clearly fits or two are equally plausible, "
        "return best_index = -1 so the retriever abstains instead of guessing."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "best_index": {"type": "integer",
                           "description": "0-based index of the single best child, or -1 if ambiguous/none fits"},
            "confidence": {"type": "number", "description": "0..1 confidence in best_index"},
        },
        "required": ["best_index", "confidence"],
    },
}


def _first_tool_use(response):
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "tool_use":
            return block
    return None


def default_node_text(g, atom):
    name = g.display_of(atom)
    if name:
        return name
    node = g.nodes.get(atom)
    return node.type_name if node else str(atom)


def llm_scorer(client, *, model=MODEL, node_text=default_node_text, max_tokens=512):
    """A descend scorer backed by a real Claude model. The Anthropic `client` is
    dependency-injected — pass a live `anthropic.Anthropic()` in production or a scripted fake
    in tests; the algebra + gate + sealing are identical either way. For each internal node it
    asks the model which child section best answers the query and how confident it is, then
    maps that to a per-child NONCONFORMITY score (HIGH = more likely wrong). Ambiguity
    (best_index = -1) or low confidence keeps every child high, so the conformal gate abstains
    instead of hallucinating a branch — the exact failure mode this design exists to prevent."""

    def scorer(g, _node, children, query):
        titles = [node_text(g, c) for c in children]
        listing = "\n".join(f"[{i}] {t}" for i, t in enumerate(titles))
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=("You navigate a document's table of contents to locate an answer. Pick the one "
                    "child section to descend into, and prefer abstaining (best_index = -1) over a "
                    "wrong guess."),
            tools=[RANK_TOOL],
            tool_choice={"type": "tool", "name": "rank_child_section"},
            messages=[{"role": "user",
                       "content": f"Query: {query}\n\nCandidate child sections:\n{listing}"}],
        )
        tu = _first_tool_use(response)
        scores = {c: 1.0 for c in children}  # default high (abstain) unless a confident in-range pick
        if tu is not None:
            best = tu.input.get("best_index", -1)
            conf = float(tu.input.get("confidence", 0.0))
            if isinstance(best, int) and 0 <= best < len(children):
                scores[children[best]] = max(0.0, 1.0 - conf)
        return scores

    return scorer


# --------------------------------------------------------------------------- #
# CLI — end-to-end demo: answer a multi-hop query with a signed, cited receipt.
# --------------------------------------------------------------------------- #
def _default_gate(alpha):
    """A split-CRC gate calibrated so a confident pick (score ~0.1) is accepted and an
    ambiguous one (~0.9) abstains, at risk budget `alpha`."""
    scores = [i / 100 for i in range(100)]
    correct = [s <= 0.4 for s in scores]
    return cg.calibrate(scores, correct, alpha)


def _live_client():
    import anthropic  # noqa: PLC0415  (lazy: only when actually using --model)

    return anthropic.Anthropic()


def _report(result, artifact, disposition, answer_label=None):
    lines = [
        f"verdict         : {result.verdict}  →  StopGate {artifact['verdict']}  ({disposition})",
        f"evidence grade  : {result.egrade}",
        f"answer          : {answer_label or result.answer}",
        f"doubly grounded : {result.doubly_grounded}",
        f"citations       : {result.citations}",
        f"witness         : {result.witness}",
        f"artifact_id     : {sg.artifact_id(artifact)}",
        "trace           :",
    ]
    lines += [f"    {step}" for step in result.trace]
    return "\n".join(lines)


def cmd_retrieve(args):
    import json  # noqa: PLC0415

    with open(args.bundle, encoding="utf-8") as fh:
        fragment = json.load(fh)
    g = fp.project(fragment)
    start = g.id_map[(fragment["tenant_id"], args.start)]
    scorer = llm_scorer(_live_client()) if args.model else keyword_scorer()
    visible = label_gate(args.cleared) if args.cleared else allow_all
    result = retrieve_edge(
        g, start, args.rel, scorer=scorer, gate=_default_gate(args.alpha), query=args.query,
        beam_k=args.beam_k, e_floor=args.e_floor, visible=visible)
    signer = (sg.Signer.from_seed(bytes.fromhex(args.key_seed), args.key_id)
              if args.key_seed else sg.Signer.generate(args.key_id))
    artifact, disposition = seal_episode(
        result, signer=signer, session_id=args.session_id, workcell_id=args.workcell_id,
        window_start=args.window_start, window_end=args.window_end, evaluated_at=args.evaluated_at)
    answer_label = g.display_of(result.answer) if result.answer is not None else None
    print(json.dumps(artifact, indent=2, ensure_ascii=False) if args.json
          else _report(result, artifact, disposition, answer_label))
    return 0


def build_parser():
    import argparse  # noqa: PLC0415

    p = argparse.ArgumentParser(
        prog="fiber_retrieval",
        description="Fibered retrieval: cross a fiber boundary, locate page anchors, verdict the "
                    "cross-document claim, and seal a signed, cited receipt.")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("retrieve", help="Run traverse;descend;verdict;seal on a fiber bundle.")
    r.add_argument("--bundle", required=True, help="Crystal Atlas fiber-bundle JSON (fragment).")
    r.add_argument("--start", required=True, help="Start node_id to hop from.")
    r.add_argument("--rel", required=True, help="Relational edge type to traverse (E_R).")
    r.add_argument("--query", required=True, help="Retrieval query (guides descend).")
    r.add_argument("--model", action="store_true",
                   help="Use a live Claude branch scorer (default: deterministic keyword navigator).")
    r.add_argument("--alpha", type=float, default=0.10, help="Conformal risk budget.")
    r.add_argument("--beam-k", type=int, default=8, dest="beam_k")
    r.add_argument("--e-floor", default="sampled", dest="e_floor",
                   choices=["sampled", "verified", "exact"])
    r.add_argument("--cleared", nargs="*", default=None,
                   help="WallGuard confidentiality labels the caller is cleared for.")
    r.add_argument("--key-seed", dest="key_seed", default=None,
                   help="32-byte ed25519 seed (hex) for the signer; else ephemeral.")
    r.add_argument("--key-id", dest="key_id", default="fiber-retrieval")
    r.add_argument("--session-id", dest="session_id", default="fiber-cli")
    r.add_argument("--workcell-id", dest="workcell_id", default="fiber-cli")
    r.add_argument("--window-start", dest="window_start", default="2026-07-04T00:00:00Z")
    r.add_argument("--window-end", dest="window_end", default="2026-07-04T00:00:01Z")
    r.add_argument("--evaluated-at", dest="evaluated_at", default=None)
    r.add_argument("--json", action="store_true", help="Emit the signed StopGate artifact JSON.")
    r.set_defaults(func=cmd_retrieve)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
