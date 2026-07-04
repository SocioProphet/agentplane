#!/usr/bin/env python3
"""Narration fidelity verifier — P4 claim comparison + P5 composition (WO-4).

The product surface of SP-TRACE-CFR: given an agent's narration claims and the
control-flow structure R_H recovered from the sealed replay segment, decide per
claim whether the narration is faithful, and emit the verdict as a signed
StepGateArtifact. A NEG (the agent claimed a structure it did not run) also emits
a ReasoningFailureTrace.

Pipeline position: recover_hammock -> [this] -> step_gate. The verdict is a pure
harness function of evidence (v = g_H(e)); the model only supplied the claim.

  alpha : ClaimIR -> AST(Π)         (§2 D5) — the clause tree is already a Π-AST
  P4 comparison (§4.4)              — claimed primitive vs recovered over the span;
                                       equalities: SEQ assoc, SWITCH case order, IF arm
                                       swap w/ negation. WHILE != DO_WHILE, IF != IF_ELSE.
  P5 composition (§4.5)             — R_H POS/ZERO/NEG (R_I absent => ZERO) -> finding.

Verdict projection (axis binding): POS->finding OK(->PASS), NEG(semantic)->VIOLATION,
ZERO->None(->INDETERMINATE, REVIEW iff gate-relevant). Stdlib-only.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step_gate  # noqa: E402
import stopgate_artifact as sg  # noqa: E402

POS, ZERO, NEG = "POS", "ZERO", "NEG"

# per-claim verdict -> VerifierIR finding (step_gate then maps finding -> StepGate verdict)
_VERDICT_TO_FINDING = {POS: "OK", NEG: "VIOLATION", ZERO: None}


@dataclass
class ClaimVerdict:
    claim_id: str
    verdict: str
    reason: str
    claimed_primitive: str | None = None
    recovered_primitive: str | None = None


def alpha(claim_ir: dict):
    """Compile ClaimIR to a Π-AST. The `clause` is already structured; return it,
    or None if the claim is unstructured (ZERO / CLAIM_UNSTRUCTURED)."""
    clause = claim_ir.get("clause")
    if not clause or "primitive" not in clause:
        return None
    return clause


def _span_node_ids(covers, events) -> set[str] | None:
    if not covers or len(covers) != 2:
        return None
    ids = [e["event_id"] for e in events]
    try:
        i0, i1 = ids.index(covers[0]), ids.index(covers[1])
    except ValueError:
        return None
    lo, hi = min(i0, i1), max(i0, i1)
    return {f"{events[k]['site_id']}#{events[k]['kind']}" for k in range(lo, hi + 1)}


def _region_over(node_ids, recovery):
    """The recovered region with the greatest overlap with the span."""
    best, best_ov = None, 0
    for r in recovery.regions:
        ov = len(r.nodes & node_ids)
        if ov > best_ov:
            best, best_ov = r, ov
    return best


def verify_claim(claim_ir: dict, events: list[dict], recovery) -> ClaimVerdict:
    cid = claim_ir.get("claim_id", "?")
    ast = alpha(claim_ir)
    if ast is None:
        return ClaimVerdict(cid, ZERO, "CLAIM_UNSTRUCTURED")
    node_ids = _span_node_ids(claim_ir.get("covers"), events)
    if node_ids is None:
        return ClaimVerdict(cid, ZERO, "CLAIM_UNANCHORED", claimed_primitive=ast["primitive"])

    region = _region_over(node_ids, recovery)
    claimed = ast["primitive"]
    if region is None:
        return ClaimVerdict(cid, ZERO, "SPAN_UNRECOVERED", claimed_primitive=claimed)
    if region.verdict == ZERO:
        return ClaimVerdict(cid, ZERO, "RECOVERED_ZERO", claimed, region.primitive)
    if claimed == region.primitive:
        return ClaimVerdict(cid, POS, "MATCH", claimed, region.primitive)
    return ClaimVerdict(cid, NEG, "STRUCTURE_MISMATCH", claimed, region.primitive)


def emit_stepgate(cv: ClaimVerdict, signer, session_id: str = "", gate_relevant: bool = False):
    """Emit a signed StepGateArtifact for the claim's composed verdict (§5 binding)."""
    finding = _VERDICT_TO_FINDING[cv.verdict]
    if cv.verdict == ZERO and gate_relevant:
        finding = "REVIEW"
    ev = [sg.Evidence(source_event_uuid=cv.claim_id, evidence_hash=sg.sha256_evidence(cv.reason), layer="semantic")]
    return step_gate.build_step_gate(
        node_id=cv.claim_id, tier=1, finding=finding, evidence=ev, signer=signer,
        session_id=session_id, predicate=f"narration_fidelity:{cv.claimed_primitive}",
    )


def reasoning_failure_trace(cv: ClaimVerdict, session_id: str = "") -> dict:
    """§5.2: a NEG additionally emits a ReasoningFailureTrace."""
    assert cv.verdict == NEG
    return {
        "apiVersion": "agentplane/v0.1",
        "kind": "ReasoningFailureTrace",
        "trace_id": f"nft-{cv.claim_id}",
        "verifier_decision": "VIOLATION",
        "failure_cluster": "GOV-NARR-STRUCT-001",
        "claim_refs": [cv.claim_id],
        "failure_annotation": f"claimed {cv.claimed_primitive}, ran {cv.recovered_primitive}",
    }


def verify_all(claims: list[dict], events: list[dict], recovery, signer, session_id: str = ""):
    """Verify every claim; return (claim_verdicts, stepgate_artifacts, failure_traces)."""
    verdicts = [verify_claim(c, events, recovery) for c in claims]
    gates = [emit_stepgate(v, signer, session_id) for v in verdicts]
    traces = [reasoning_failure_trace(v, session_id) for v in verdicts if v.verdict == NEG]
    return verdicts, gates, traces
