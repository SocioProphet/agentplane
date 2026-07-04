#!/usr/bin/env python3
"""P0 — ingest & segment sealing for SP-TRACE-CFR (WO-1, SPEC §4.0).

Reads raw JSONL bytes of a control-flow segment, computes the segment_hash over
the raw bytes BEFORE trusting the parse, and enforces the P0 invariants. A segment
that violates any invariant is rendered INDETERMINATE — there is NO repair (repair
of a malformed evidence log is evidence tampering).

Invariants (all reported; status is INDETERMINATE if any fire):
  * MALFORMED_JSON     — a line does not parse
  * MISSING_FIELD      — an event lacks event_id/session_id/agent_id/site_id/kind/ts_mono_ns/payload_hash
  * NON_MONOTONE_TS    — ts_mono_ns not strictly increasing within an agent_id
  * DUPLICATE_EVENT_ID — an event_id repeats
  * DANGLING_PARENT    — parent_event_id refers to no earlier event
  * SEAL_MISMATCH      — a provided expected_hash != the computed segment_hash

Pairs with tools/trace_cfr_emitter.py (its seal() output round-trips to SEALED here).
Stdlib-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

REQUIRED_FIELDS = ("event_id", "session_id", "agent_id", "site_id", "kind", "ts_mono_ns", "payload_hash")

STATUS_SEALED = "SEALED"
STATUS_INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class IngestResult:
    status: str
    segment_hash: str
    events: list[dict] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_SEALED


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def ingest(raw_jsonl: bytes, expected_hash: str | None = None) -> IngestResult:
    """Seal + validate a raw JSONL segment. No repair."""
    segment_hash = _sha256(raw_jsonl)  # over raw bytes, BEFORE parsing
    reasons: list[str] = []

    if expected_hash is not None and expected_hash != segment_hash:
        reasons.append(f"SEAL_MISMATCH: expected {expected_hash} got {segment_hash}")

    lines = [ln for ln in raw_jsonl.split(b"\n") if ln.strip()]
    if not lines:
        return IngestResult(STATUS_INDETERMINATE, segment_hash, [], reasons + ["EMPTY"])

    events: list[dict] = []
    for i, ln in enumerate(lines):
        try:
            events.append(json.loads(ln))
        except (json.JSONDecodeError, ValueError):
            reasons.append(f"MALFORMED_JSON: line {i}")

    seen_ids: set[str] = set()
    last_ts: dict[str, int] = {}
    for ev in events:
        missing = [f for f in REQUIRED_FIELDS if f not in ev]
        if missing:
            reasons.append(f"MISSING_FIELD: {ev.get('event_id', '?')} lacks {missing}")
            continue
        eid = ev["event_id"]
        if eid in seen_ids:
            reasons.append(f"DUPLICATE_EVENT_ID: {eid}")
        agent = ev["agent_id"]
        ts = ev["ts_mono_ns"]
        if agent in last_ts and ts <= last_ts[agent]:
            reasons.append(f"NON_MONOTONE_TS: {eid} ts={ts} <= {last_ts[agent]} for {agent}")
        last_ts[agent] = ts
        parent = ev.get("parent_event_id")
        if parent is not None and parent not in seen_ids:
            reasons.append(f"DANGLING_PARENT: {eid} -> {parent}")
        seen_ids.add(eid)

    status = STATUS_SEALED if not reasons else STATUS_INDETERMINATE
    return IngestResult(status, segment_hash, events if status == STATUS_SEALED else [], reasons)


def ingest_sealed_segment(segment: dict) -> IngestResult:
    """Re-derive raw JSONL from a sealed segment dict and verify against its stored hash."""
    raw = b"".join(
        json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
        for e in segment.get("events", [])
    )
    return ingest(raw, expected_hash=segment.get("segment", {}).get("segment_hash"))
