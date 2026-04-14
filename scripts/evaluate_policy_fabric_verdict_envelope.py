#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


class VerdictEnvelopeError(RuntimeError):
    """Raised when the Policy Fabric verdict envelope cannot be evaluated safely."""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def evaluate_verdict_envelope(envelope_path: Path) -> dict[str, Any]:
    if not envelope_path.exists():
        raise VerdictEnvelopeError(f"verdict envelope missing: {envelope_path}")

    envelope = _load_json(envelope_path)

    if envelope.get("kind") != "PolicyFabricVerdictEnvelope":
        raise VerdictEnvelopeError("verdict envelope kind must be PolicyFabricVerdictEnvelope")

    for key in ("capturedAt", "policyBundle", "domain", "promote", "fit", "verdictArtifactRef", "verdictExplanationRef"):
        if key not in envelope:
            raise VerdictEnvelopeError(f"verdict envelope missing required field: {key}")

    policy_bundle = envelope.get("policyBundle") or {}
    for key in ("id", "version"):
        if key not in policy_bundle:
            raise VerdictEnvelopeError(f"verdict envelope policyBundle missing required field: {key}")

    fit = envelope.get("fit")
    if fit not in {"surjection", "injection", "bijection"}:
        raise VerdictEnvelopeError("verdict envelope fit must be one of surjection, injection, bijection")

    promote = bool(envelope.get("promote"))
    artifact = {
        "kind": "PolicyFabricVerdictGateArtifact",
        "evaluatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "result": "allow" if promote else "deny",
        "reason": "promote=true" if promote else "promote=false",
        "domain": envelope.get("domain"),
        "rightsCritical": bool(envelope.get("rightsCritical", False)),
        "fit": fit,
        "failedPredicates": envelope.get("failedPredicates") or [],
        "policyBundle": policy_bundle,
        "verdictEnvelopePath": str(envelope_path.resolve()),
        "verdictArtifactRef": envelope.get("verdictArtifactRef"),
        "verdictExplanationRef": envelope.get("verdictExplanationRef")
    }
    return artifact


def write_gate_artifact(artifact: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a Policy Fabric verdict envelope.")
    parser.add_argument("verdict_envelope_json", help="Path to the verdict envelope JSON")
    parser.add_argument("--artifact-path", default=None, help="Optional output path for the gate artifact")
    args = parser.parse_args()

    envelope_path = Path(args.verdict_envelope_json)
    artifact = evaluate_verdict_envelope(envelope_path)

    out_path = Path(args.artifact_path) if args.artifact_path else envelope_path.parent / "policy-fabric-verdict-gate-artifact.json"
    write_gate_artifact(artifact, out_path)
    print(f"[policy-fabric-gate] {artifact['result'].upper()}: wrote {out_path}")
    if artifact["result"] != "allow":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
