#!/usr/bin/env python3
"""StepGateArtifact — per-node signed gate (composition §9).

Identical signed-attestation semantics to StopGateArtifact, emitted per
obligation-graph node, applying the StopGate Tier-0/Tier-1 budget split along the
TIME axis rather than the compile/runtime axis:

  * Tier-0 (cheap, trajectory-level): short-circuit on violation — verdict
    VIOLATION sets short_circuit=True so downstream compute is skipped.
  * Tier-1 (turn-level): consistency check of the node output vs upstream evidence.

`promise` (P[step achieves obligation]) and `progress` (predecessor interdependence)
are ADVISORY scores (AgentPRM) and MAY be model-emitted; the verdict is a pure
function of the harness finding — v = g_H(e), §14.3 — and promise/progress never
enter it. Reuses tools/stopgate_artifact.py ed25519 signing so step gates verify
with the same machinery. Conforms to schemas/stepgate-artifact.schema.v0.1.json.
"""

from __future__ import annotations

from typing import Any

try:
    import stopgate_artifact as sg
except ImportError:  # run-as-script / load-by-path
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import stopgate_artifact as sg

VERDICTS = ("OK", "REVIEW", "VIOLATION", "INDETERMINATE")
HARNESS_KINDS = ("deterministic-harness", "human-authority")

# Verdict is derived from the VerifierIR finding by harness code only (never authored
# by the model, never a function of promise/progress). This is the whole gate function.
_FINDING_TO_VERDICT: dict[Any, str] = {
    "OK": "OK",
    "VIOLATION": "VIOLATION",
    "REVIEW": "REVIEW",
    None: "INDETERMINATE",  # no bindable evidence
}


def derive_verdict(finding: str | None) -> str:
    """g_H over a finding: the pure verdict function (§14.3). No side inputs."""
    if finding not in _FINDING_TO_VERDICT:
        raise ValueError(f"unknown VerifierIR finding: {finding!r}")
    return _FINDING_TO_VERDICT[finding]


def build_step_gate(
    *,
    node_id: str,
    tier: int,
    finding: str | None,
    evidence: list[Any],
    signer: "sg.Signer",
    predicate: str = "",
    gate_id: str = "",
    session_id: str = "",
    subject: Any = None,
    promise: float | None = None,
    progress: float | None = None,
    evaluated_by: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit a signed StepGateArtifact for one obligation-graph node."""
    if tier not in (0, 1):
        raise ValueError("tier must be 0 or 1")
    eb = evaluated_by or {"kind": "deterministic-harness"}
    if eb.get("kind") not in HARNESS_KINDS:
        raise ValueError("§14.3 model-exclusion: evaluated_by.kind must be harness/human-authority")

    verdict = derive_verdict(finding)
    artifact: dict[str, Any] = {
        "spec_version": sg.SPEC_VERSION,
        "node_id": node_id,
        "gate_id": gate_id,
        "session_id": session_id,
        "subject": subject,
        "predicate": predicate,
        "tier": tier,
        "verdict": verdict,
        # Tier-0 short-circuits downstream compute the moment a violation is seen.
        "short_circuit": bool(tier == 0 and verdict == "VIOLATION"),
        "evidence": [e.to_dict() if hasattr(e, "to_dict") else e for e in evidence],
        "evaluated_by": eb,
        "evaluated_at": sg.utc_now_iso(),
    }
    if promise is not None:
        artifact["promise"] = promise
    if progress is not None:
        artifact["progress"] = progress

    artifact["signature"] = signer.signature_block(sg.canonical_bytes(artifact))
    return artifact


def verify_step_gate(artifact: dict[str, Any], keyring: "sg.Keyring") -> tuple[bool, list[str]]:
    """Independent re-check: signature + §14.3 gate-factorization + verdict domain."""
    problems: list[str] = []
    if artifact.get("evaluated_by", {}).get("kind") not in HARNESS_KINDS:
        problems.append("§14.3 model-exclusion: verdict not attributed to harness/human")
    if artifact.get("verdict") not in VERDICTS:
        problems.append(f"verdict {artifact.get('verdict')!r} not in {VERDICTS}")
    if artifact.get("tier") not in (0, 1):
        problems.append("tier not in {0,1}")
    sig = artifact.get("signature") or {}
    body = {k: v for k, v in artifact.items() if k != "signature"}
    if not (sig and keyring.verify(sig.get("key_id", ""), sg.canonical_bytes(body), sig.get("value", ""))):
        problems.append("signature invalid or missing")
    return (not problems), problems


def should_short_circuit(artifact: dict[str, Any]) -> bool:
    """Tier-0 continuation gate: skip downstream compute iff the node short-circuited."""
    return bool(artifact.get("short_circuit"))
