#!/usr/bin/env python3
"""Reference live agent runtime that emits control-flow ReasoningEvents (step 2).

The verifier + bridge + spec vocabulary are in place; what was missing was a runtime
that actually EXECUTES an agent loop and emits the control-flow events live (not from a
fixture). This is that runtime: a small ReAct-style executor over a tool set driven by a
`policy`, which emits sourceos-spec ReasoningEvents (with `controlFlow`, camelCase) as a
side effect of execution. The control flow EMERGES from tool results — a retry loop runs
as many iterations as the tool takes to succeed — so the event stream is real, not authored.

Honest scope: the `policy` is where a model goes; here it is a deterministic Python
callable (no LLM in agentplane). Swapping in a real policy changes nothing downstream —
the runtime already emits the canonical events, and attest() runs the full narration gate.
Privacy posture preserved: only operational structure is emitted, never raw reasoning.
Stdlib-only.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import attest_governed_run  # noqa: E402
import stopgate_artifact as sg  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class AgentRuntime:
    """Executes an agent loop and emits control-flow ReasoningEvents live."""

    def __init__(self, run_id: str, agent_id: str = "agent-0"):
        self.run_id = run_id
        self.run_ref = f"urn:srcos:reasoning-run:{run_id}"
        self.agent_id = agent_id
        self._seq = 0
        self._events: list[dict] = []
        self.claims: list[dict] = []

    def _emit(self, event_type: str, control_flow: dict, *, trust: str = "trusted-control-input",
              trace: str = "workspace-safe", summary: str = "") -> str:
        eid = f"urn:srcos:reasoning-event:{self.run_id}-{self._seq}"
        self._events.append({
            "id": eid, "type": "ReasoningEvent", "specVersion": "2.0.0", "runRef": self.run_ref,
            "eventType": event_type, "summary": summary, "traceLevel": trace, "trustLevel": trust,
            "capturedAt": _now(), "controlFlow": control_flow,
        })
        self._seq += 1
        return eid

    # ---- execution primitives (the loop / agent calls these as it acts) ----
    def call_tool(self, name: str, arg: str | None = None, trust: str = "trusted-control-input") -> str:
        cf = {"site": name}
        if arg:
            cf["arg"] = arg
        return self._emit("reasoning.tool.called", cf, trust=trust, summary=f"called {name}")

    def branch(self, site: str, taken: str, guard_position: str | None = None) -> str:
        cf = {"site": site, "branchTaken": taken}
        if guard_position:
            cf["guardPosition"] = guard_position
        return self._emit("reasoning.decision.branched", cf, summary=f"branch {site}={taken}")

    @contextmanager
    def subrun(self, site: str, sidechain_id: str):
        self._emit("reasoning.subrun.spawned", {"site": site, "sidechainId": sidechain_id})
        try:
            yield sidechain_id
        finally:
            self._emit("reasoning.subrun.joined", {"site": site, "sidechainId": sidechain_id})

    def complete(self, site: str = "exit") -> str:
        return self._emit("reasoning.run.completed", {"site": site})

    def narrate(self, claim_id: str, primitive: str, covers: list[str], raw: str = "") -> None:
        self.claims.append({"claim_id": claim_id, "covers": covers, "clause": {"primitive": primitive}, "raw": raw})

    def events(self) -> list[dict]:
        return list(self._events)

    # ---- the loop ----
    def run_react(self, policy, tools: dict, max_steps: int = 100) -> list[dict]:
        """Drive a ReAct-style loop: policy(state) -> action; execute + emit; repeat.

        Actions: ('tool', name, arg) | ('branch', site, taken, guard) | ('done',).
        Control flow (how many iterations, which branches) emerges from tool results."""
        state: dict = {"step": 0, "history": []}
        while state["step"] < max_steps:
            action = policy(state)
            if action[0] == "tool":
                _, name, arg = (action + (None,))[:3]
                result = tools[name](state)
                self.call_tool(name, arg)
                state["history"].append((name, result))
                state["last_result"] = result
            elif action[0] == "branch":
                _, site, taken, guard = (action + (None,))[:4]
                self.branch(site, taken, guard)
            elif action[0] == "done":
                break
            state["step"] += 1
        self.complete()
        return self.events()

    # ---- gate the run ----
    def attest(self, signer: "sg.Signer | None" = None):
        signer = signer or sg.Signer.from_seed(b"\x07" * 32, key_id="dev-harness")
        return attest_governed_run.attest_run(self._events, self.claims, signer, session_id=self.run_id)
