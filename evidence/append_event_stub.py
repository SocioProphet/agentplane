#!/usr/bin/env python3
"""Append-only evidence journal for the first local-hybrid slice.

Durability contract: `appended` is true only after the record has been written
to the journal and fsync'd, and `journalOffset` is the real byte offset at which
that record starts. Both are observable facts about a file on disk — earlier
revisions of this module returned `appended: True` with an offset synthesized
from the payload digest while performing no I/O at all, which meant every
consumer of `journalOffset` (notably replay/materialize_cairn_stub.py, which
builds `cairn://<task>/<offset>` replay handles) referenced a journal position
that had never existed.

Records are hash-chained: each carries the previous record's chain digest, so a
rewritten or removed record is detectable rather than merely discouraged by
opening the file in append mode. This mirrors source-os/runtime/triune-anchor's
rolling root (`root = sha256(previous_root || entry_hash)`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_JOURNAL = Path(".agentplane/evidence-journal.jsonl")
GENESIS = "0" * 64


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _strip_prefix(digest: str) -> str:
    return digest.split(":", 1)[1] if ":" in digest else digest


def tip_digest(journal_path: Path) -> str:
    """Chain digest of the last record, or the genesis value on an empty journal."""
    if not journal_path.exists():
        return GENESIS
    last = None
    with journal_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    if last is None:
        return GENESIS
    return _strip_prefix(json.loads(last)["chainDigest"])


def append_event(payload: dict[str, Any], journal_path: Path = DEFAULT_JOURNAL) -> dict[str, Any]:
    """Append one evidence record and return its real offset and digests."""
    event = payload.get("event", payload)
    digest = hashlib.sha256(canonical_bytes(event)).hexdigest()

    journal_path.parent.mkdir(parents=True, exist_ok=True)
    previous = tip_digest(journal_path)
    chain = hashlib.sha256(f"{previous}{digest}".encode("utf-8")).hexdigest()

    record = {
        "appendedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "chainDigest": f"sha256:{chain}",
        "evidenceDigest": f"sha256:{digest}",
        "event": event,
        "previousDigest": f"sha256:{previous}",
    }

    # Offset is taken before the write so it marks where this record starts.
    journal_offset = journal_path.stat().st_size if journal_path.exists() else 0
    with journal_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())

    return {
        "appended": True,
        "journalOffset": journal_offset,
        "evidenceDigest": f"sha256:{digest}",
        "chainDigest": f"sha256:{chain}",
    }


def verify_journal(journal_path: Path) -> dict[str, Any]:
    """Recompute the chain and report the first break, if any."""
    if not journal_path.exists():
        return {"verified": False, "reason": "journal does not exist", "records": 0}

    previous = GENESIS
    count = 0
    with journal_path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            record = json.loads(line)
            recorded_previous = _strip_prefix(record["previousDigest"])
            if recorded_previous != previous:
                return {"verified": False, "reason": "previousDigest mismatch",
                        "recordIndex": index, "records": count}

            # Re-derive the evidence digest from the event body. Without this the
            # chain would only prove the sequence of digests is intact, not that
            # each digest still describes its event — editing an event in place
            # while leaving its recorded digest alone would verify clean.
            event_digest = hashlib.sha256(canonical_bytes(record["event"])).hexdigest()
            if event_digest != _strip_prefix(record["evidenceDigest"]):
                return {"verified": False, "reason": "evidenceDigest mismatch",
                        "recordIndex": index, "records": count}

            expected = hashlib.sha256(
                f"{previous}{event_digest}".encode("utf-8")
            ).hexdigest()
            if expected != _strip_prefix(record["chainDigest"]):
                return {"verified": False, "reason": "chainDigest mismatch",
                        "recordIndex": index, "records": count}
            previous = expected
            count += 1
    return {"verified": True, "records": count, "tip": f"sha256:{previous}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("payload", type=Path, nargs="?")
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL,
                        help=f"Append-only journal path (default: {DEFAULT_JOURNAL})")
    parser.add_argument("--verify", action="store_true",
                        help="Verify the journal hash chain instead of appending.")
    args = parser.parse_args()

    if args.verify:
        result = verify_journal(args.journal)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["verified"] else 1

    if args.payload is None:
        parser.error("payload is required unless --verify is given")

    result = append_event(load_json(args.payload), args.journal)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
