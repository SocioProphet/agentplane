#!/usr/bin/env python3
"""Tests for the append-only evidence journal.

These assert the durability contract that the previous revision claimed but did
not hold: a record reported as appended is on disk, and `journalOffset` is the
real byte offset where that record starts — not a value derived from the digest.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO / "evidence" / "append_event_stub.py"

spec = importlib.util.spec_from_file_location("append_event_stub", MODULE_PATH)
assert spec and spec.loader
append_event_stub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(append_event_stub)


@pytest.fixture()
def journal(tmp_path: Path) -> Path:
    return tmp_path / "evidence-journal.jsonl"


def read_records(journal_path: Path) -> list[dict]:
    return [json.loads(line) for line in journal_path.read_text().splitlines() if line.strip()]


def test_append_actually_writes(journal: Path) -> None:
    result = append_event_stub.append_event({"event": {"kind": "run.started"}}, journal)

    assert result["appended"] is True
    assert journal.exists(), "appended:True must mean the journal exists"
    records = read_records(journal)
    assert len(records) == 1
    assert records[0]["event"] == {"kind": "run.started"}


def test_journal_offset_is_a_real_byte_offset(journal: Path) -> None:
    """The offset must locate the record in the file, not encode its digest."""
    first = append_event_stub.append_event({"event": {"n": 1}}, journal)
    second = append_event_stub.append_event({"event": {"n": 2}}, journal)

    assert first["journalOffset"] == 0
    raw = journal.read_bytes()
    # Seeking to the reported offset must land exactly on the second record.
    assert second["journalOffset"] == len(raw.split(b"\n")[0]) + 1
    recovered = json.loads(raw[second["journalOffset"]:].split(b"\n")[0])
    assert recovered["event"] == {"n": 2}


def test_offsets_are_monotonic_and_distinct(journal: Path) -> None:
    """Two callers of the same event must not collide — the old stub did."""
    same = {"event": {"kind": "duplicate"}}
    first = append_event_stub.append_event(same, journal)
    second = append_event_stub.append_event(same, journal)

    assert first["evidenceDigest"] == second["evidenceDigest"], "same event, same digest"
    assert second["journalOffset"] > first["journalOffset"], "but distinct positions"
    assert len(read_records(journal)) == 2


def test_chain_links_records(journal: Path) -> None:
    append_event_stub.append_event({"event": {"n": 1}}, journal)
    append_event_stub.append_event({"event": {"n": 2}}, journal)

    records = read_records(journal)
    assert records[0]["previousDigest"] == f"sha256:{append_event_stub.GENESIS}"
    assert records[1]["previousDigest"] == records[0]["chainDigest"]

    verdict = append_event_stub.verify_journal(journal)
    assert verdict["verified"] is True
    assert verdict["records"] == 2


def test_verify_detects_tampering(journal: Path) -> None:
    append_event_stub.append_event({"event": {"n": 1}}, journal)
    append_event_stub.append_event({"event": {"n": 2}}, journal)

    records = read_records(journal)
    records[0]["event"] = {"n": "tampered"}
    journal.write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records) + "\n"
    )

    verdict = append_event_stub.verify_journal(journal)
    assert verdict["verified"] is False
    assert verdict["reason"] == "evidenceDigest mismatch"


def test_verify_detects_removed_record(journal: Path) -> None:
    for n in range(3):
        append_event_stub.append_event({"event": {"n": n}}, journal)

    records = read_records(journal)
    del records[1]
    journal.write_text(
        "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records) + "\n"
    )

    verdict = append_event_stub.verify_journal(journal)
    assert verdict["verified"] is False
    assert verdict["reason"] == "previousDigest mismatch"


def test_verify_reports_missing_journal(journal: Path) -> None:
    verdict = append_event_stub.verify_journal(journal)
    assert verdict["verified"] is False
    assert verdict["records"] == 0
