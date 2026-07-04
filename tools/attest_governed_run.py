#!/usr/bin/env python3
"""Governed-run narration-fidelity attestation (the governed-runner integration).

The governed runner assembles run *evidence* (Contract -> Preflight -> Admission ->
evidence folder -> Dossier); its non-goals explicitly exclude agent/verifier execution.
So SP-TRACE-CFR integrates the honest way: it produces an evidence artifact ABOUT a
run's narration fidelity, computed from the run's recorded control-flow actions, and
binds it into the run's evidence folder.

Pipeline: control-flow ReasoningEvents (bridge format) -> trace-cfr segment -> both
engines -> narration compare -> folded run verdict -> one signed run attestation, which
is written as `narration-fidelity-attestation.json` in the attempt/evidence folder.
Fails closed. Stdlib-only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trace_cfr_reasoning_bridge as bridge  # noqa: E402
import trace_cfr_runtime as rt  # noqa: E402

ATTESTATION_FILENAME = "narration-fidelity-attestation.json"


def attest_run(events: list[dict], claims: list[dict], signer, session_id: str = ""):
    """Compute the signed narration-fidelity attestation for a governed run.

    Returns (attestation, RunFidelityReport). `events` are control-flow ReasoningEvents
    (the run's recorded actions); `claims` are the agent's narration ClaimIRs."""
    segment = bridge.reasoning_events_to_segment(events, session_id=session_id)
    report = rt.gate_segment(segment, claims, signer, session_id=session_id)
    attestation = rt.build_run_attestation(report, signer, session_id=session_id)
    return attestation, report


def write_attestation(attestation: dict, run_dir: str | os.PathLike) -> Path:
    """Bind the attestation into a run's evidence folder."""
    path = Path(run_dir) / ATTESTATION_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(attestation, indent=2, sort_keys=True), encoding="utf-8")
    return path
