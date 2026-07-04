#!/usr/bin/env python3
"""Narration-fidelity runtime gate — the deployable capability (SP-TRACE-CFR).

This is what a governed agent runner calls. During a run the agent (or the runner
wrapping it) records its control flow and its narration claims through a
RunRecorder; at end-of-run finish() seals the segment and runs the whole verifier
stack (ingest -> CFG -> normalize -> R_H + R_I -> narration comparison), aggregates
a single run-level gate verdict via the §4 receipt fold (most-cautious-wins), and
fails closed if the narration does not match what the agent actually did.

There is no live model loop yet (we are building the platform); the recorder is the
integration seam a real runner drives, and is exercised here by simulated runs. The
harness signing key is supplied by the deployment; a deterministic default is used
only for local/dev. Stdlib-only.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration_fidelity_verifier as nfv  # noqa: E402
import receipt_fold as rf  # noqa: E402
import recover_hammock as rh  # noqa: E402
import recover_interval as ri  # noqa: E402
import stopgate_artifact as sg  # noqa: E402
import trace_cfr_cfg as cfg  # noqa: E402
import trace_cfr_emitter as em  # noqa: E402
import trace_cfr_ingest as ing  # noqa: E402
import trace_cfr_normalize as norm  # noqa: E402

# per-claim verdict -> StopGate verdict domain, folded by verdict_monoid (§4)
_CLAIM_TO_GATE = {nfv.POS: "PASS", nfv.NEG: "FAIL", nfv.ZERO: "INDETERMINATE", nfv.INDETERMINATE: "INDETERMINATE"}


@dataclass
class RunFidelityReport:
    gate_verdict: str                     # PASS | FAIL | REVIEW | INDETERMINATE (folded)
    claim_verdicts: list = field(default_factory=list)
    stepgates: list = field(default_factory=list)
    failure_traces: list = field(default_factory=list)
    segment: dict | None = None
    reason: str = ""

    @property
    def permitted(self) -> bool:
        return self.gate_verdict == "PASS"


class RunRecorder:
    """Integration seam a governed runner drives during an agent run."""

    def __init__(self, session_id: str, agent_id: str = "agent-0", signer: "sg.Signer | None" = None):
        self.session_id = session_id
        self.em = em.TraceCfrEmitter(session_id, agent_id)
        self.claims: list[dict] = []
        # deployment supplies the harness key; deterministic default for local/dev only
        self.signer = signer or sg.Signer.from_seed(b"\x07" * 32, key_id="dev-harness")

    # ---- control-flow recording (the runner calls these as the agent acts) ----
    def tool_call(self, site: str, payload=None):
        return self.em.tool_call(site, payload)

    def decision(self, site: str, branch_taken: str, guard_position: str | None = None, payload=None):
        return self.em.decision(site, branch_taken, guard_position, payload)

    def sidechain(self, site: str, sidechain_id: str):
        return self.em.sidechain(site, sidechain_id)

    def terminal(self, site: str = "exit"):
        return self.em.terminal(site)

    # ---- narration (the agent's claim about what it did over a span) ----
    def narrate(self, claim_id: str, primitive: str, covers: list[str], raw: str = ""):
        self.claims.append({"claim_id": claim_id, "covers": covers, "clause": {"primitive": primitive}, "raw": raw})

    # ---- end of run: seal, verify, gate ----
    def finish(self) -> RunFidelityReport:
        return gate_segment(self.em.seal(), self.claims, self.signer, self.session_id)


def gate_segment(segment: dict, claims: list[dict], signer: "sg.Signer", session_id: str = "") -> RunFidelityReport:
    """Gate an already-sealed segment + its narration claims. The reusable core the
    RunRecorder and the `sp-run narration-gate` CLI both call."""
    r = ing.ingest_sealed_segment(segment)
    if not r.ok:
        return RunFidelityReport("INDETERMINATE", reason=f"ingest: {r.reasons}", segment=segment)
    g = cfg.build_cfg(r.events)
    n = norm.normalize(g)
    rh_rec = rh.recover_hammock(g, n)
    ri_rec = ri.recover_interval(g, n)
    verdicts, gates, traces = nfv.verify_all(
        claims, r.events, rh_rec, signer, session_id=session_id, ri_recovery=ri_rec
    )
    mapped = [_CLAIM_TO_GATE[v.verdict] for v in verdicts]
    gate = rf.fold(mapped, rf.verdict_monoid) if mapped else "PASS"
    return RunFidelityReport(
        gate_verdict=gate, claim_verdicts=verdicts, stepgates=gates,
        failure_traces=traces, segment=segment,
        reason="ok" if gate == "PASS" else f"{sum(1 for v in verdicts if v.verdict == nfv.NEG)} unfaithful claim(s)",
    )
