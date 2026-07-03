#!/usr/bin/env python3
"""Reference implementation of the formal StopGateArtifact (spec v0.1).

A StopGateArtifact is a signed, evidence-bound attestation, emitted by
deterministic harness code, that a named gate condition was evaluated against
hashed ground-truth evidence. A `lift_authority` permits a side-effecting action
by *verifying the artifact*, not by trusting a model's narration.

This module provides:

  * canonical serialization + sha256 evidence hashing;
  * an ed25519 signer/verifier with a small key-id keyring;
  * a deterministic evaluator that maps a VerifierIR finding to a verdict (§4)
    and applies the invariant degradations (§5);
  * an independent verifier that re-checks the five invariants and the signature
    at consume time and returns the action disposition;
  * attributed human-authority override construction (§5.5);
  * an emit / verify / keygen CLI.

It reimplements no guardrail policy and contacts no model provider. See
docs/StopGateArtifact.spec.v0.1.md and schemas/StopGateArtifact.schema.v0.1.json.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ed25519 signing uses an embedded, stdlib-only RFC 8032 implementation, so this
# module has zero third-party dependencies and stays CI-portable. Signatures are
# deterministic and interoperable with any conformant ed25519 verifier. The sibling
# is loaded robustly whether this file is run as a script, imported as a module, or
# loaded by path (the repo's test convention uses importlib.spec_from_file_location).
try:
    import ed25519_pure
except ImportError:
    import os as _os

    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import ed25519_pure

SPEC_VERSION = "0.1"
ARTIFACT_TYPE = "StopGateArtifact"

# §4 — verdict domain, sourced from the VerifierIR finding (never authored freely).
FINDING_OK = "OK"
FINDING_VIOLATION = "VIOLATION"
FINDING_REVIEW = "REVIEW"
FINDING_NONE = None  # no evidence bindable at all

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_REVIEW = "REVIEW"
VERDICT_INDETERMINATE = "INDETERMINATE"

FINDING_TO_VERDICT: dict[str | None, str] = {
    FINDING_OK: VERDICT_PASS,
    FINDING_VIOLATION: VERDICT_FAIL,
    FINDING_REVIEW: VERDICT_REVIEW,
    FINDING_NONE: VERDICT_INDETERMINATE,
}

# §4 — disposition of the gated action for each verdict.
DISPOSITION = {
    VERDICT_PASS: "permit",
    VERDICT_FAIL: "deny",
    VERDICT_REVIEW: "deny-pending-human",
    VERDICT_INDETERMINATE: "deny-require-override",
}

PERMIT_ELIGIBLE = {VERDICT_PASS}
LAYERS = {"semantic", "transport"}
HARNESS_KIND = "deterministic-harness"
HUMAN_KIND = "human-authority"


# --------------------------------------------------------------------------- #
# Canonicalization + hashing
# --------------------------------------------------------------------------- #
def canonical_bytes(obj: Any) -> bytes:
    """Deterministic serialization: sorted keys, no insignificant whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _without(obj: dict[str, Any], key: str) -> dict[str, Any]:
    clone = copy.deepcopy(obj)
    clone.pop(key, None)
    return clone


def sha256_evidence(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# --------------------------------------------------------------------------- #
# Signing
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Signer:
    key_id: str
    _seed: bytes  # 32-byte ed25519 private seed

    @classmethod
    def from_seed(cls, seed: bytes, key_id: str) -> "Signer":
        if len(seed) != 32:
            raise ValueError("ed25519 seed must be exactly 32 bytes")
        return cls(key_id=key_id, _seed=bytes(seed))

    @classmethod
    def generate(cls, key_id: str) -> "Signer":
        import os

        return cls(key_id=key_id, _seed=os.urandom(32))

    def public_bytes(self) -> bytes:
        return ed25519_pure.public_from_seed(self._seed)

    def public_b64(self) -> str:
        return base64.b64encode(self.public_bytes()).decode("ascii")

    def sign_bytes(self, data: bytes) -> str:
        return base64.b64encode(ed25519_pure.sign(self._seed, data)).decode("ascii")

    def signature_block(self, data: bytes) -> dict[str, str]:
        return {"alg": "ed25519", "key_id": self.key_id, "value": self.sign_bytes(data)}


class Keyring:
    """Maps key_id -> raw ed25519 public key bytes, for independent verification."""

    def __init__(self) -> None:
        self._keys: dict[str, bytes] = {}

    def add(self, key_id: str, public_bytes: bytes) -> "Keyring":
        if len(public_bytes) != 32:
            raise ValueError("ed25519 public key must be 32 bytes")
        self._keys[key_id] = public_bytes
        return self

    def add_b64(self, key_id: str, public_b64: str) -> "Keyring":
        return self.add(key_id, base64.b64decode(public_b64))

    def add_signer(self, signer: Signer) -> "Keyring":
        return self.add(signer.key_id, signer.public_bytes())

    def verify(self, key_id: str, data: bytes, signature_b64: str) -> bool:
        pub = self._keys.get(key_id)
        if pub is None:
            return False
        try:
            return ed25519_pure.verify(pub, data, base64.b64decode(signature_b64))
        except (ValueError, TypeError):
            return False


# --------------------------------------------------------------------------- #
# Evidence + evaluator inputs
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Evidence:
    source_event_uuid: str
    evidence_hash: str
    layer: str
    signal: str | None = None
    mode: str = "presence"  # presence | absence  (§5.4)
    observed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "source_event_uuid": self.source_event_uuid,
            "evidence_hash": self.evidence_hash,
            "layer": self.layer,
            "mode": self.mode,
        }
        if self.signal is not None:
            d["signal"] = self.signal
        if self.observed_at is not None:
            d["observed_at"] = self.observed_at
        return d


@dataclass
class CompletenessAttestation:
    asserted: bool
    basis: str
    attested_by: str
    signature: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "asserted": self.asserted,
            "basis": self.basis,
            "attested_by": self.attested_by,
        }
        if self.signature is not None:
            d["signature"] = self.signature
        return d


# --------------------------------------------------------------------------- #
# §5 — invariant enforcement (emit-side degradation)
# --------------------------------------------------------------------------- #
def _completeness_ok(att: CompletenessAttestation | None, keyring: Keyring | None) -> bool:
    if att is None or att.asserted is not True:
        return False
    if att.signature is not None:
        if keyring is None:
            return False
        body = canonical_bytes(_without(att.to_dict(), "signature"))
        return keyring.verify(att.signature["key_id"], body, att.signature["value"])
    return True  # §5.4 as written: a self-claimed attestation licenses closed-world (open item 10.4).


def degrade_verdict(
    raw_verdict: str,
    evidence: list[Evidence],
    predicate_layer: str,
    completeness: CompletenessAttestation | None,
    keyring: Keyring | None = None,
) -> tuple[str, list[str]]:
    """Apply §5.3 / §5.4 degradations. A permit/deny may drop to REVIEW; never lifts."""
    notes: list[str] = []
    verdict = raw_verdict
    if verdict in (VERDICT_PASS, VERDICT_FAIL):
        # 5.3 layer binding: a predicate binds to its layer; needs >=1 entry there.
        if not any(ev.layer == predicate_layer for ev in evidence):
            notes.append(
                f"5.3 layer-binding: no {predicate_layer}-layer evidence backs verdict -> degraded to REVIEW"
            )
            verdict = VERDICT_REVIEW
        # 5.4 closed-world: absence-based finding needs a valid completeness attestation.
        elif any(ev.mode == "absence" for ev in evidence) and not _completeness_ok(completeness, keyring):
            notes.append(
                "5.4 completeness: absence-based finding without valid completeness attestation -> degraded to REVIEW"
            )
            verdict = VERDICT_REVIEW
    return verdict, notes


# --------------------------------------------------------------------------- #
# Emit
# --------------------------------------------------------------------------- #
def build_unsigned(
    *,
    gate_id: str,
    session_id: str,
    workcell_id: str,
    subject: list[str],
    predicate: str,
    verdict: str,
    evidence: list[Evidence],
    evaluated_by: dict[str, str],
    evaluated_at: str,
    window_start: str,
    window_end: str,
    lift_authority: str,
    predicate_layer: str = "semantic",
    completeness: CompletenessAttestation | None = None,
    obligations: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Deterministic harness must never emit a temporally-incoherent artifact (§5.2).
    ws, we, ea = parse_iso(window_start), parse_iso(window_end), parse_iso(evaluated_at)
    if not (ws <= we <= ea):
        raise ValueError("§5.2 temporal precedence: require window.start <= window.end <= evaluated_at")
    if evaluated_by.get("kind") not in (HARNESS_KIND, HUMAN_KIND):
        raise ValueError("§5.1 model-exclusion: evaluated_by.kind must be deterministic-harness or human-authority")

    artifact: dict[str, Any] = {
        "type": ARTIFACT_TYPE,
        "spec_version": SPEC_VERSION,
        "gate_id": gate_id,
        "session_id": session_id,
        "workcell_id": workcell_id,
        "subject": list(subject),
        "predicate": predicate,
        "predicate_layer": predicate_layer,
        "verdict": verdict,
        "evidence": [ev.to_dict() for ev in evidence],
        "evaluated_by": dict(evaluated_by),
        "evaluated_at": evaluated_at,
        "evidence_window": {"start": window_start, "end": window_end},
        "lift_authority": lift_authority,
        "obligations": list(obligations or []),
    }
    if completeness is not None:
        artifact["log_completeness_attestation"] = completeness.to_dict()
    if extra:
        artifact.update(extra)
    return artifact


def sign_artifact(artifact: dict[str, Any], signer: Signer) -> dict[str, Any]:
    signed = copy.deepcopy(artifact)
    signed.pop("signature", None)
    signed["signature"] = signer.signature_block(canonical_bytes(signed))
    return signed


def evaluate(
    *,
    finding: str | None,
    evidence: list[Evidence],
    signer: Signer,
    gate_id: str,
    session_id: str,
    workcell_id: str,
    subject: list[str],
    predicate: str,
    evaluated_by: dict[str, str],
    lift_authority: str,
    window_start: str,
    window_end: str,
    evaluated_at: str | None = None,
    predicate_layer: str = "semantic",
    completeness: CompletenessAttestation | None = None,
    obligations: list[str] | None = None,
    keyring: Keyring | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Deterministic emit: finding -> verdict (§4) -> degrade (§5) -> sign."""
    if finding not in FINDING_TO_VERDICT:
        raise ValueError(f"unknown VerifierIR finding: {finding!r}")
    evaluated_at = evaluated_at or utc_now_iso()
    raw = FINDING_TO_VERDICT[finding]
    verdict, notes = degrade_verdict(raw, evidence, predicate_layer, completeness, keyring)
    unsigned = build_unsigned(
        gate_id=gate_id,
        session_id=session_id,
        workcell_id=workcell_id,
        subject=subject,
        predicate=predicate,
        verdict=verdict,
        evidence=evidence,
        evaluated_by=evaluated_by,
        evaluated_at=evaluated_at,
        window_start=window_start,
        window_end=window_end,
        lift_authority=lift_authority,
        predicate_layer=predicate_layer,
        completeness=completeness,
        obligations=obligations,
    )
    return sign_artifact(unsigned, signer), notes


def build_override(
    denied_artifact: dict[str, Any],
    *,
    operator: dict[str, Any],
    signer: Signer,
    basis: str,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """§5.5 — attributed human override. A second artifact, human-authority, that
    references the denying artifact. There is no un-attributed path to a side effect."""
    if not operator.get("id"):
        raise ValueError("§5.5 override requires an attributed operator.id")
    evaluated_at = evaluated_at or utc_now_iso()
    window = denied_artifact["evidence_window"]
    unsigned = build_unsigned(
        gate_id=denied_artifact["gate_id"],
        session_id=denied_artifact["session_id"],
        workcell_id=denied_artifact["workcell_id"],
        subject=denied_artifact["subject"],
        predicate=denied_artifact["predicate"],
        verdict=VERDICT_PASS,  # the human lifts the gate
        evidence=[],
        evaluated_by={"component": "operator.override", "version": SPEC_VERSION + ".0", "kind": HUMAN_KIND},
        evaluated_at=evaluated_at,
        window_start=window["start"],
        window_end=window["end"],
        lift_authority=denied_artifact["lift_authority"],
        predicate_layer=denied_artifact.get("predicate_layer", "semantic"),
        obligations=denied_artifact.get("obligations"),
        extra={
            "override_of": artifact_id(denied_artifact),
            "operator": operator,
            "log_completeness_attestation": {
                "asserted": False,
                "basis": basis,
                "attested_by": operator["id"],
            },
        },
    )
    return sign_artifact(unsigned, signer)


def artifact_id(artifact: dict[str, Any]) -> str:
    """Content address of an artifact including its signature (its ledger identity)."""
    return sha256_evidence(canonical_bytes(artifact))


# --------------------------------------------------------------------------- #
# Verify (consume-side, independent re-check of §5 + signature)
# --------------------------------------------------------------------------- #
@dataclass
class VerifyResult:
    ok: bool
    verdict: str
    disposition: str
    signature_valid: bool
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verdict": self.verdict,
            "disposition": self.disposition,
            "signature_valid": self.signature_valid,
            "violations": self.violations,
        }


def verify_artifact(
    artifact: dict[str, Any],
    keyring: Keyring,
    *,
    action_start: str | None = None,
) -> VerifyResult:
    """Re-derive the disposition from the artifact alone. Any invariant breach or a
    bad signature invalidates a permit — a lie can never lift the gate."""
    violations: list[str] = []
    verdict = artifact.get("verdict", VERDICT_INDETERMINATE)
    evaluated_by = artifact.get("evaluated_by") or {}
    kind = evaluated_by.get("kind")
    is_override = kind == HUMAN_KIND

    # 5.1 model-exclusion
    if kind not in (HARNESS_KIND, HUMAN_KIND):
        violations.append(f"5.1 model-exclusion: evaluated_by.kind={kind!r} is not a permitted authority")

    # 5.5 override attribution
    if is_override:
        if not artifact.get("override_of"):
            violations.append("5.5 override: human-authority artifact missing override_of")
        if not (artifact.get("operator") or {}).get("id"):
            violations.append("5.5 override: human-authority artifact missing operator.id")

    # 5.2 temporal precedence
    window = artifact.get("evidence_window") or {}
    try:
        ws, we = parse_iso(window["start"]), parse_iso(window["end"])
        ea = parse_iso(artifact["evaluated_at"])
        if not (ws <= we):
            violations.append("5.2 temporal: window.start must be <= window.end")
        if not (we <= ea):
            violations.append("5.2 temporal: window.end must be <= evaluated_at")
        for ev in artifact.get("evidence", []):
            obs = ev.get("observed_at")
            if obs is not None and not (ws <= parse_iso(obs) <= we):
                violations.append(f"5.2 temporal: evidence {ev.get('source_event_uuid')} observed outside window")
        if action_start is not None and not (we <= parse_iso(action_start)):
            violations.append("5.2 temporal: evidence_window.end must be <= start of the gated action")
    except (KeyError, ValueError) as exc:
        violations.append(f"5.2 temporal: unparseable window/timestamps ({exc})")

    evidence = artifact.get("evidence", [])
    predicate_layer = artifact.get("predicate_layer", "semantic")

    # 5.3 / 5.4 bind a PASS/FAIL to evidence. A human-authority override (§5.5) is
    # evidence-less by construction — its authority is the attributed operator, not a
    # payload — so the evidence-binding invariants apply only to harness verdicts.
    if verdict in (VERDICT_PASS, VERDICT_FAIL) and not is_override:
        if not any(ev.get("layer") == predicate_layer for ev in evidence):
            violations.append(
                f"5.3 layer-binding: {verdict} on a {predicate_layer} predicate lacks {predicate_layer}-layer evidence"
            )
        # 5.4 completeness-gated closed-world
        if any(ev.get("mode") == "absence" for ev in evidence):
            att_dict = artifact.get("log_completeness_attestation")
            att = (
                CompletenessAttestation(
                    asserted=att_dict.get("asserted", False),
                    basis=att_dict.get("basis", ""),
                    attested_by=att_dict.get("attested_by", ""),
                    signature=att_dict.get("signature"),
                )
                if att_dict
                else None
            )
            if not _completeness_ok(att, keyring):
                violations.append(
                    "5.4 completeness: absence-based PASS/FAIL without a valid completeness attestation"
                )

    # Signature
    sig = artifact.get("signature")
    signature_valid = False
    if not sig:
        violations.append("signature: missing")
    else:
        body = canonical_bytes(_without(artifact, "signature"))
        signature_valid = keyring.verify(sig.get("key_id", ""), body, sig.get("value", ""))
        if not signature_valid:
            violations.append(f"signature: does not verify against key_id={sig.get('key_id')!r}")

    disposition = DISPOSITION.get(verdict, "deny")
    # A permit is only honoured if the artifact is wholly sound.
    if violations and disposition == "permit":
        disposition = "deny"
    ok = not violations
    return VerifyResult(
        ok=ok, verdict=verdict, disposition=disposition, signature_valid=signature_valid, violations=violations
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_keygen(args: argparse.Namespace) -> int:
    signer = (
        Signer.from_seed(bytes.fromhex(args.seed), args.key_id) if args.seed else Signer.generate(args.key_id)
    )
    print(json.dumps({"key_id": signer.key_id, "public_b64": signer.public_b64()}, indent=2))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    artifact = _load_json(args.artifact)
    keyring = Keyring()
    for entry in args.key or []:
        key_id, pub_b64 = entry.split("=", 1)
        keyring.add_b64(key_id, pub_b64)
    result = verify_artifact(artifact, keyring, action_start=args.action_start)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.ok and result.disposition == "permit" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit / verify formal StopGateArtifacts (spec v0.1).")
    sub = parser.add_subparsers(dest="command", required=True)

    kg = sub.add_parser("keygen", help="Generate or derive an ed25519 signing key.")
    kg.add_argument("--key-id", required=True)
    kg.add_argument("--seed", help="32-byte hex seed for a reproducible key (optional).")
    kg.set_defaults(func=_cmd_keygen)

    vf = sub.add_parser("verify", help="Independently verify an artifact and print its disposition.")
    vf.add_argument("--artifact", required=True)
    vf.add_argument("--key", action="append", metavar="key_id=public_b64", help="A public key to trust.")
    vf.add_argument("--action-start", help="ISO timestamp of the gated action's start (enforces §5.2).")
    vf.set_defaults(func=_cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
