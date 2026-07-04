#!/usr/bin/env python3
"""Bridge: sourceos-spec ReasoningEvents -> trace-cfr segment (the path to real data).

AUDIT FINDING (2026-07-04): the existing sourceos-spec reasoning-evidence stream is
too coarse to feed SP-TRACE-CFR directly. `ReasoningRun` has `eventRefs` + `safeTrace`
but no step/trace array, and the only emitted `eventType` is `reasoning.run.created`
-- there is NO control-flow event vocabulary. So the verifier cannot run on live
reasoning data until emitters produce control-flow events.

This module defines the EMIT-SIDE CONTRACT that closes that gap and proves the path:
a small control-flow eventType vocabulary (a proposed sourceos-spec extension) plus a
`controlFlow` field on the event, which the bridge projects into a trace-cfr segment.
It also wires the vocab that DOES already exist: `trustLevel` -> the §11 taint integrity
lattice, and `traceLevel` -> the disclosure tier (privacy vocab is intentional; honored).

Once TurtleTerm/Noetica/BearBrowser/the governed runner emit these eventTypes, the
narration-fidelity gate runs on real runs with zero further change. Stdlib-only.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import taint_lattice as tl  # noqa: E402
import trace_cfr_emitter as em  # noqa: E402

# Proposed control-flow eventType vocabulary (sourceos-spec reasoning-event extension).
CONTROL_FLOW_EVENT_TYPES = {
    "reasoning.tool.called": "tool_call",
    "reasoning.decision.branched": "decision",
    "reasoning.subrun.spawned": "spawn",
    "reasoning.subrun.joined": "join",
    "reasoning.run.completed": "terminal",
}

# trustLevel (already in ReasoningEvent) -> §11 integrity-lattice label. This is the
# real, existing vocab we wire straight into the taint admission gate.
TRUST_TO_TAINT = {
    "trusted-control-input": "TRUSTED",
    "trusted-workspace-source": "TRUSTED",
    "semi-trusted-project-source": "SANDBOXED",
    "untrusted-observation": "UNTRUSTED",
    "restricted-material": "UNTRUSTED",
}

# traceLevel -> disclosure tier (privacy vocab is intentional; carried, never widened).
TRACE_TO_DISCLOSURE = {
    "public-safe": "public",
    "workspace-safe": "workspace",
    "operator-private": "operator",
    "restricted": "restricted",
}


def taint_label(trust_level: str) -> str:
    """Map a ReasoningEvent trustLevel to an integrity label (bottom = UNTRUSTED)."""
    return TRUST_TO_TAINT.get(trust_level, "UNTRUSTED")


def reasoning_events_to_segment(events: list[dict], session_id: str = "") -> dict:
    """Project control-flow ReasoningEvents into a sealed trace-cfr segment.

    Each control-flow event carries a `controlFlow` object with the fields the
    emitter records: {site, branch_taken?, guard_position?, sidechain_id?}. Events
    are consumed in list order (already the run's causal order). Non-control-flow
    events (e.g. reasoning.run.created) are skipped. Raises if no run id is derivable.
    """
    run_ref = session_id or (events[0].get("runRef") if events else "") or "reasoning-run"
    e = em.TraceCfrEmitter(run_ref)
    open_sidechains: dict[str, object] = {}

    for ev in events:
        kind = CONTROL_FLOW_EVENT_TYPES.get(ev.get("eventType", ""))
        if kind is None:
            continue
        cf = ev.get("controlFlow", {})
        site = cf.get("site") or ev.get("id", "site")
        if kind == "tool_call":
            e.tool_call(site)
        elif kind == "decision":
            e.decision(site, cf.get("branch_taken", "unknown"), cf.get("guard_position"))
        elif kind == "spawn":
            e.spawn(site, cf.get("sidechain_id", "sc"))
        elif kind == "join":
            e.join(site, cf.get("sidechain_id", "sc"))
        elif kind == "terminal":
            e.terminal(site)
    if not e._events:
        raise ValueError("no control-flow events found; emitter must produce the CONTROL_FLOW_EVENT_TYPES")
    return e.seal(log_uri=f"reasoning://{run_ref}")


def taint_gate_from_events(events: list[dict], required: dict[str, str]) -> tuple[str, list]:
    """Run the §11 argument-taint admission using the events' trustLevels as labels.

    `required` maps arg_name -> the integrity a capability demands; the arg's actual
    label comes from the trustLevel of the event that produced it (event id -> arg via
    controlFlow.arg). Returns (finding, violations)."""
    L = tl.integrity_lattice()
    arg_labels: dict[str, str] = {}
    origins: dict[str, str] = {}
    for ev in events:
        arg = ev.get("controlFlow", {}).get("arg")
        if arg:
            arg_labels[arg] = taint_label(ev.get("trustLevel", "untrusted-observation"))
            origins[arg] = ev.get("id", "?")
    return tl.admit(arg_labels, required, L, origins=origins)
