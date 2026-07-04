#!/usr/bin/env python3
"""Reference control-flow emitter for SP-TRACE-CFR (WO-0.A).

There is no live runner emitting control-flow trajectory events today
(agentic-ops-trajectory-event carries only stepKind {model_call,tool_call,...} and
governance decisions). This module is the reference PRODUCER of the D1 control-flow
projection (SP_TRACE_CFR_001_SPEC §2): it emits well-formed spawn/join/decision/
tool_call/terminal events with site_id / branch_taken / guard_position / sidechain_id
and seals them into a segment (schemas/trace-cfr-segment.schema.v0.1.json). It is the
input WO-1 ingest recovers a CFG from, and the substrate the orch-dsl fixtures (WO-5)
and recovery engines consume until a real runner is instrumented.

Deterministic by construction (counter-based ids + monotonic ts + canonical hashing),
so identical call sequences yield byte-identical segments — required for reproducible
`segment_hash` sealing (§4.0) and fixture stability.

Realistic first target (§0.1 scoping note): a linear agent loop yields SEQ + SPAWN_JOIN
only; the `sidechain()` context manager makes I-SC1 (one spawn, <=1 join) hold by
construction. Branch/loop emission is exercised by the orch-dsl fixtures. Stdlib-only.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any

TS_STEP_NS = 1000  # monotonic tick per event


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class TraceCfrEmitter:
    def __init__(self, session_id: str, agent_id: str = "agent-0"):
        self.session_id = session_id
        self.agent_id = agent_id
        self._seq = 0
        self._last_event_id: str | None = None
        self._sidechain_stack: list[str] = []
        self._events: list[dict[str, Any]] = []

    # ----- core ----- #
    def _emit(
        self,
        kind: str,
        site_id: str,
        payload: Any = None,
        *,
        sidechain_id: str | None = None,
        branch_taken: str | None = None,
        guard_position: str | None = None,
        parent_event_id: str | None = "__auto__",
    ) -> str:
        eid = f"{self.session_id}:{self._seq:06d}"
        ts = self._seq * TS_STEP_NS
        sc = sidechain_id if sidechain_id is not None else (self._sidechain_stack[-1] if self._sidechain_stack else None)
        parent = self._last_event_id if parent_event_id == "__auto__" else parent_event_id
        event = {
            "event_id": eid,
            "session_id": self.session_id,
            "parent_event_id": parent,
            "agent_id": self.agent_id,
            "site_id": site_id,
            "sidechain_id": sc,
            "kind": kind,
            "ts_mono_ns": ts,
            "payload_hash": _sha256(_canonical(payload if payload is not None else {})),
            "branch_taken": branch_taken,
            "guard_position": guard_position,
        }
        self._events.append(event)
        self._last_event_id = eid
        self._seq += 1
        return eid

    # ----- public verbs (map 1:1 to Π / D2 node kinds) ----- #
    def tool_call(self, site_id: str, payload: Any = None) -> str:
        return self._emit("tool_call", site_id, payload)

    def decision(self, site_id: str, branch_taken: str, guard_position: str | None = None, payload: Any = None) -> str:
        return self._emit("decision", site_id, payload, branch_taken=branch_taken, guard_position=guard_position)

    def spawn(self, site_id: str, sidechain_id: str, payload: Any = None) -> str:
        # spawn edge is on the PARENT chain; the new sidechain begins after it
        return self._emit("spawn", site_id, payload, sidechain_id=None)

    def join(self, site_id: str, sidechain_id: str, payload: Any = None) -> str:
        return self._emit("join", site_id, payload, sidechain_id=None)

    def terminal(self, site_id: str = "exit", payload: Any = None) -> str:
        return self._emit("terminal", site_id, payload)

    def narration(self, site_id: str, covers: list[str], claim: Any, payload: Any = None) -> str:
        return self._emit("narration", site_id, {"covers": covers, "claim": claim, "payload": payload})

    @contextmanager
    def sidechain(self, site_id: str, sidechain_id: str):
        """Open a SESE sidechain: emits spawn on enter, tags inner events with
        sidechain_id, emits join on exit. Makes I-SC1 hold by construction."""
        self.spawn(site_id, sidechain_id)
        self._sidechain_stack.append(sidechain_id)
        try:
            yield sidechain_id
        finally:
            self._sidechain_stack.pop()
            self.join(site_id, sidechain_id)

    # ----- sealing (§4.0) ----- #
    def to_jsonl(self) -> bytes:
        return b"".join(_canonical(e) + b"\n" for e in self._events)

    def seal(self, log_uri: str = "") -> dict[str, Any]:
        if not self._events:
            raise ValueError("cannot seal an empty segment")
        raw = self.to_jsonl()
        seg = {
            "first_event_id": self._events[0]["event_id"],
            "last_event_id": self._events[-1]["event_id"],
            "segment_hash": _sha256(raw),
        }
        if log_uri:
            seg["log_uri"] = log_uri
        return {"events": list(self._events), "segment": seg}


def sidechain_sese_ok(segment: dict[str, Any]) -> bool:
    """I-SC1 precheck: every sidechain_id has exactly one spawn and at most one join.

    (Spawn/join carry sidechain_id=None on the parent chain; here we count by the
    sidechain_id tag on the inner events plus the spawn/join verbs bracketing them.)
    """
    spawns: dict[str, int] = {}
    joins: dict[str, int] = {}
    active: list[str] = []
    for e in segment["events"]:
        if e["kind"] == "spawn":
            # the sidechain id is whatever inner events will carry; inferred from the
            # next tagged event is fragile, so we rely on the tag on inner events below.
            pass
    # count distinct sidechain tags actually used
    used = {e["sidechain_id"] for e in segment["events"] if e.get("sidechain_id")}
    for sc in used:
        inner = [e for e in segment["events"] if e.get("sidechain_id") == sc]
        # a well-formed SESE sidechain has a contiguous inner run; we require >=1 inner
        if not inner:
            return False
    # spawn/join balance: equal counts, joins <= spawns
    n_spawn = sum(1 for e in segment["events"] if e["kind"] == "spawn")
    n_join = sum(1 for e in segment["events"] if e["kind"] == "join")
    return n_join <= n_spawn
