#!/usr/bin/env python3
"""Evidence-sealing authority for SourceOS ReasoningReceipts.

This tool realizes the spec's authority boundary: "SocioProphet/agentplane owns
evidence sealing and replay authority." It ingests a local SourceOS
``ReasoningReceipt`` (as emitted by TurtleTerm's turtle-agentd and Noetica into
``~/.local/state/sourceos/reasoning/<run_hex>/receipt.json``), validates it
against the canonical ``ReasoningReceipt.json`` schema, seals it into an
externally-verifiable ``SealedReasoningEvidence`` record (deterministic
hash-chain binding receipt -> run trace -> events + an agentplane attestation),
and can re-verify a sealed record for tamper-evidence.

Stdlib-only (hashlib, json, argparse, pathlib, datetime, hmac/secrets). It uses
``jsonschema`` only if it happens to be importable; otherwise it falls back to a
structural check matching the schema's required fields and constraints.

Seal:
  seal_reasoning_receipt.py --receipt R.json [--run RUN.json] [--events E.ndjson] --out-dir DIR
Verify:
  seal_reasoning_receipt.py --verify SEALED.json

The binding hash construction mirrors validate_evidence_receipt_binding.py's
intent (binding a receipt to its companion artifacts):

  seal_hash = "sha256:" + sha256(receipt_canonical || run.traceHash || events_sha)

where receipt_canonical is the sorted-keys, compact JSON encoding of the receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Locate the canonical SourceOS spec (SOURCEOS_SPEC_DIR env or ~/dev/sourceos-spec).
import os

SPEC_DIR = Path(
    os.environ.get("SOURCEOS_SPEC_DIR", str(Path.home() / "dev" / "sourceos-spec"))
)
RECEIPT_SCHEMA_PATH = SPEC_DIR / "schemas" / "ReasoningReceipt.json"

RECEIPT_ID_PREFIX = "urn:srcos:receipt:reasoning:"
RUN_REF_PREFIX = "urn:srcos:reasoning-run:"
EVIDENCE_ID_PREFIX = "urn:srcos:evidence:sealed-reasoning:"
SEALING_AUTHORITY = "urn:srcos:authority:agentplane"
SPEC_VERSION = "2.0.0"
REPLAY_CLASSES = {"exact", "best-effort", "evidence-only", "non-replayable-side-effect"}
RECEIPT_REQUIRED = (
    "id",
    "type",
    "specVersion",
    "runRef",
    "taskRef",
    "status",
    "traceHash",
    "replayClass",
    "capturedAt",
)
RECEIPT_STATUSES = {"completed", "failed", "blocked", "cancelled"}


class SealError(Exception):
    """Raised when sealing or verification cannot proceed."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    """Deterministic, sorted-keys, compact JSON encoding (house convention)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SealError(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SealError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SealError(f"expected JSON object in {path}")
    return data


# ---------------------------------------------------------------------------
# Receipt validation
# ---------------------------------------------------------------------------


def _structural_validate(receipt: dict[str, Any]) -> None:
    missing = [field for field in RECEIPT_REQUIRED if field not in receipt]
    if missing:
        raise SealError(f"missing required field(s): {', '.join(missing)}")
    if receipt.get("type") != "ReasoningReceipt":
        raise SealError(f"type must be 'ReasoningReceipt', got {receipt.get('type')!r}")
    receipt_id = str(receipt.get("id", ""))
    if not receipt_id.startswith(RECEIPT_ID_PREFIX):
        raise SealError(f"id must start with {RECEIPT_ID_PREFIX!r}")
    run_ref = str(receipt.get("runRef", ""))
    if not run_ref.startswith(RUN_REF_PREFIX):
        raise SealError(f"runRef must start with {RUN_REF_PREFIX!r}")
    replay_class = receipt.get("replayClass")
    if replay_class not in REPLAY_CLASSES:
        raise SealError(
            f"replayClass must be one of {sorted(REPLAY_CLASSES)}, got {replay_class!r}"
        )
    status = receipt.get("status")
    if status not in RECEIPT_STATUSES:
        raise SealError(
            f"status must be one of {sorted(RECEIPT_STATUSES)}, got {status!r}"
        )
    if not isinstance(receipt.get("traceHash"), str) or not receipt["traceHash"]:
        raise SealError("traceHash must be a non-empty string")
    if not isinstance(receipt.get("specVersion"), str) or not receipt["specVersion"]:
        raise SealError("specVersion must be a non-empty string")


def validate_receipt(receipt: dict[str, Any]) -> None:
    """Validate the receipt; prefer jsonschema if importable, else structural."""
    try:
        import jsonschema  # type: ignore
    except Exception:
        _structural_validate(receipt)
        return

    if not RECEIPT_SCHEMA_PATH.exists():
        # No schema on disk to drive jsonschema; fall back structurally.
        _structural_validate(receipt)
        return
    schema = load_json_object(RECEIPT_SCHEMA_PATH)
    try:
        jsonschema.validate(instance=receipt, schema=schema)
    except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
        # Surface a compact reason.
        raise SealError(str(exc).splitlines()[0]) from exc


# ---------------------------------------------------------------------------
# Seal construction
# ---------------------------------------------------------------------------


def events_sha(events_path: Path | None) -> str:
    """sha256 over the raw events ndjson file bytes, or empty-string sentinel."""
    if events_path is None:
        return ""
    if not events_path.exists():
        raise SealError(f"missing events file: {events_path}")
    return sha256_hex(events_path.read_bytes())


def compute_binding(
    receipt: dict[str, Any],
    run: dict[str, Any] | None,
    events_path: Path | None,
) -> tuple[str, dict[str, str]]:
    """Compute the seal hash + binding triple.

    seal_hash = sha256( receipt_canonical || run_trace_hash || events_sha )

    receipt_trace_hash falls back to the receipt's own traceHash when no run
    is supplied (the receipt already embeds the run's trace hash).
    """
    receipt_canonical = canonical_bytes(receipt)
    receipt_hash = "sha256:" + sha256_hex(receipt_canonical)

    if run is not None:
        run_trace_hash = str(run.get("traceHash") or receipt.get("traceHash") or "")
    else:
        run_trace_hash = str(receipt.get("traceHash") or "")

    ev_sha = events_sha(events_path)
    events_hash = ("sha256:" + ev_sha) if ev_sha else ""

    seal_material = receipt_canonical + run_trace_hash.encode("utf-8") + ev_sha.encode("utf-8")
    seal_hash = "sha256:" + sha256_hex(seal_material)

    binding = {
        "receiptHash": receipt_hash,
        "runTraceHash": run_trace_hash,
        "eventsHash": events_hash,
    }
    return seal_hash, binding


def build_sealed_record(
    receipt: dict[str, Any],
    run: dict[str, Any] | None,
    events_path: Path | None,
    sealed_at: str | None = None,
) -> dict[str, Any]:
    seal_hash, binding = compute_binding(receipt, run, events_path)
    sealed_hex = sha256_hex(seal_hash.encode("utf-8"))
    record: dict[str, Any] = {
        "id": EVIDENCE_ID_PREFIX + sealed_hex,
        "type": "SealedReasoningEvidence",
        "specVersion": SPEC_VERSION,
        "sealedAt": sealed_at or now_utc(),
        "sealingAuthority": SEALING_AUTHORITY,
        "receiptRef": receipt["id"],
        "runRef": receipt["runRef"],
        "replayClass": receipt["replayClass"],
        "sealHash": seal_hash,
        "binding": binding,
        "receipt": receipt,
        "verifyHint": "recompute sealHash over receipt||runTraceHash||eventsHash",
    }
    return record


def recompute_seal(record: dict[str, Any]) -> str:
    """Re-derive the seal hash from an embedded receipt + binding triple.

    The verify path cannot re-read the original events file, so it trusts the
    binding's runTraceHash/eventsHash but recomputes the receipt canonical hash
    from the embedded receipt. Any mutation of the embedded receipt changes the
    canonical bytes and therefore the seal hash -> tamper-evident.
    """
    receipt = record.get("receipt")
    if not isinstance(receipt, dict):
        raise SealError("sealed record is missing an embedded receipt object")
    binding = record.get("binding")
    if not isinstance(binding, dict):
        raise SealError("sealed record is missing a binding object")

    receipt_canonical = canonical_bytes(receipt)
    run_trace_hash = str(binding.get("runTraceHash", ""))
    events_hash = str(binding.get("eventsHash", ""))
    # eventsHash is stored as "sha256:<hex>" or ""; the seal material uses the
    # bare hex (matching events_sha()'s return at seal time).
    ev_sha = events_hash.split(":", 1)[1] if events_hash.startswith("sha256:") else ""

    seal_material = receipt_canonical + run_trace_hash.encode("utf-8") + ev_sha.encode("utf-8")
    return "sha256:" + sha256_hex(seal_material)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


def append_ledger(out_dir: Path, record: dict[str, Any], sealed_path: Path) -> None:
    """Append a one-line pointer to the sealed-evidence index ledger."""
    ledger = out_dir / "sealed-index.ndjson"
    entry = {
        "evidence_id": record["id"],
        "receiptRef": record["receiptRef"],
        "runRef": record["runRef"],
        "sealHash": record["sealHash"],
        "sealedAt": record["sealedAt"],
        "sealed_path": str(sealed_path),
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_seal(args: argparse.Namespace) -> int:
    out: dict[str, Any]
    try:
        receipt = load_json_object(Path(args.receipt))
        validate_receipt(receipt)
    except SealError as exc:
        out = {"sealed": False, "reason": f"receipt failed validation: {exc}"}
        print(json.dumps(out))
        return 1

    run: dict[str, Any] | None = None
    events_path: Path | None = None
    try:
        if args.run:
            run = load_json_object(Path(args.run))
        if args.events:
            events_path = Path(args.events)
            if not events_path.exists():
                raise SealError(f"missing events file: {events_path}")
    except SealError as exc:
        out = {"sealed": False, "reason": f"companion artifact error: {exc}"}
        print(json.dumps(out))
        return 1

    record = build_sealed_record(receipt, run, events_path)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sealed_hex = record["id"][len(EVIDENCE_ID_PREFIX):]
    sealed_path = out_dir / f"{sealed_hex}.sealed.json"
    sealed_path.write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    append_ledger(out_dir, record, sealed_path)

    print(
        json.dumps(
            {
                "sealed": True,
                "evidence_id": record["id"],
                "sealed_path": str(sealed_path),
                "seal_hash": record["sealHash"],
            }
        )
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        record = load_json_object(Path(args.verify))
    except SealError as exc:
        print(json.dumps({"verified": False, "reason": str(exc)}))
        return 1

    evidence_id = record.get("id")

    # 1. Re-validate the embedded receipt against the schema.
    receipt = record.get("receipt")
    if not isinstance(receipt, dict):
        print(
            json.dumps(
                {
                    "verified": False,
                    "evidence_id": evidence_id,
                    "reason": "missing embedded receipt",
                }
            )
        )
        return 1
    try:
        validate_receipt(receipt)
    except SealError as exc:
        print(
            json.dumps(
                {
                    "verified": False,
                    "evidence_id": evidence_id,
                    "reason": f"embedded receipt failed validation: {exc}",
                }
            )
        )
        return 1

    # 2. Recompute the seal and compare.
    try:
        recomputed = recompute_seal(record)
    except SealError as exc:
        print(
            json.dumps(
                {"verified": False, "evidence_id": evidence_id, "reason": str(exc)}
            )
        )
        return 1

    stored = record.get("sealHash")
    if recomputed != stored:
        print(
            json.dumps(
                {
                    "verified": False,
                    "evidence_id": evidence_id,
                    "reason": (
                        "seal hash mismatch: embedded evidence has been altered "
                        f"(recomputed {recomputed} != stored {stored})"
                    ),
                }
            )
        )
        return 1

    print(json.dumps({"verified": True, "evidence_id": evidence_id}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seal_reasoning_receipt.py",
        description=(
            "Seal a SourceOS ReasoningReceipt into externally-verifiable "
            "SealedReasoningEvidence, or verify a sealed record (tamper-evident)."
        ),
    )
    parser.add_argument("--receipt", help="Path to the ReasoningReceipt JSON to seal.")
    parser.add_argument("--run", help="Optional path to the companion ReasoningRun (run.json).")
    parser.add_argument(
        "--events", help="Optional path to the companion reasoning-events ndjson."
    )
    parser.add_argument("--out-dir", help="Output directory for the sealed record + ledger.")
    parser.add_argument(
        "--verify", help="Path to a *.sealed.json record to verify instead of sealing."
    )
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verify:
        return cmd_verify(args)

    if not args.receipt or not args.out_dir:
        parser.error("seal mode requires --receipt and --out-dir (or use --verify)")
    return cmd_seal(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
