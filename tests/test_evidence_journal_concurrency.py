"""Concurrency tests for evidence/append_event_stub.append_event.

The defect these tests pin: before the fcntl.flock fix, two concurrent writers
observed the same `previous` tip, both computed `chainDigest` from it, and both
wrote — the chain silently BRANCHED at that point and verify_journal broke at
the second record. Same class as the ledger fix in evidence-intake-kernel.

A separate defect: `journalOffset` was taken via `Path.stat().st_size` BEFORE
opening the file for the append — a TOCTOU where another writer extended the
file between the stat and the write meant the returned offset pointed into the
middle of another record.

Both defects are latent unless the same journal is written by concurrent
processes/threads — which is the scenario every real emitter (agent_runtime +
a concurrent CLI append) creates.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from evidence.append_event_stub import append_event, verify_journal


def _worker(journal: Path, thread_id: int, events_per_thread: int) -> list[dict]:
    """Append N events, capture each append's returned offset + digest."""
    results = []
    for i in range(events_per_thread):
        results.append(
            append_event(
                {"event": {"kind": "test", "thread": thread_id, "idx": i}},
                journal_path=journal,
            )
        )
    return results


def _run_concurrent_appends(journal: Path, threads: int, per_thread: int) -> list[dict]:
    """Run `threads` threads each appending `per_thread` events; join and return."""
    out: list[list[dict]] = [[] for _ in range(threads)]

    def _entry(tid: int) -> None:
        out[tid] = _worker(journal, tid, per_thread)

    ts = [threading.Thread(target=_entry, args=(t,)) for t in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return [r for group in out for r in group]


def test_concurrent_appends_verify_clean(tmp_path: Path) -> None:
    """20 threads × 5 events each = 100 records; the chain must verify clean and
    record count must equal thread_count × events_per_thread. Any lost or
    branched record blows up here."""
    journal = tmp_path / "j.jsonl"
    _run_concurrent_appends(journal, threads=20, per_thread=5)
    result = verify_journal(journal)
    assert result["verified"], f"chain broken under concurrency: {result}"
    assert result["records"] == 100, f"lost {100 - result['records']} events"


def test_returned_offsets_are_distinct_and_point_at_starts(tmp_path: Path) -> None:
    """Every appended record's `journalOffset` must be the true byte offset at
    which its record starts. Under the old stat-before-write pattern, concurrent
    writers observed the same offset and every downstream reader dereferenced
    garbage. Pin this by asserting each returned offset maps to a line whose
    chainDigest matches what the append returned."""
    journal = tmp_path / "j.jsonl"
    results = _run_concurrent_appends(journal, threads=10, per_thread=10)
    assert len(results) == 100

    offsets = [r["journalOffset"] for r in results]
    assert len(set(offsets)) == len(offsets), "duplicate offsets — TOCTOU regression"

    # Every returned offset must sit at the start of the line whose chainDigest
    # it claims. This is the invariant `cairn://<task>/<offset>` handles depend on.
    raw = journal.read_bytes()
    for r in results:
        chunk = raw[r["journalOffset"]:]
        first_newline = chunk.index(b"\n")
        record = json.loads(chunk[:first_newline].decode("utf-8"))
        assert record["chainDigest"] == r["chainDigest"], (
            f"offset {r['journalOffset']} does not point at record {r['chainDigest']}"
        )


def test_single_writer_appends_still_work(tmp_path: Path) -> None:
    """Sanity — the concurrency fix must not regress the single-writer path."""
    journal = tmp_path / "j.jsonl"
    r1 = append_event({"event": {"kind": "x", "n": 1}}, journal_path=journal)
    r2 = append_event({"event": {"kind": "x", "n": 2}}, journal_path=journal)
    assert r1["appended"] and r2["appended"]
    assert r1["journalOffset"] == 0
    assert r2["journalOffset"] > 0
    result = verify_journal(journal)
    assert result["verified"] and result["records"] == 2


def test_empty_journal_bootstraps_to_genesis(tmp_path: Path) -> None:
    """The first record's previousDigest must be the genesis constant."""
    journal = tmp_path / "j.jsonl"
    append_event({"event": {"kind": "bootstrap"}}, journal_path=journal)
    with journal.open("r", encoding="utf-8") as h:
        record = json.loads(h.readline())
    assert record["previousDigest"] == "sha256:" + "0" * 64
