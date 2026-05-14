#!/usr/bin/env python3
"""Validate SEM-K / SCTControlProfile contracts.

This tool deliberately avoids external dependencies so it can run in AgentPlane CI
with only Python. It validates sidecar profile shape, canonical profile hash,
audience/expiry/key status, motif-to-projection semantics, and replay drift.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_MOTIFS = {"gate", "channel", "river", "bridge", "neck", "fork", "seal", "rupture", "chapel", "court"}
ALLOWED_DELIVERY = {"mcp-sidecar", "a2a-envelope", "local-host-context", "zero-trust-selective-delivery"}
ALLOWED_FAIL_MODES = {"deny", "degrade", "human-escalate", "audit-only"}
ALLOWED_MEMORY_SCOPES = {"none", "local-only", "session", "workspace"}
ALLOWED_DISCLOSURE_SCOPES = {"minimal", "bounded", "expanded"}
ALLOWED_AUDIT_MODES = {"off", "standard", "strict"}


class SemanticControlError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SemanticControlError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SemanticControlError(f"{path} must contain a JSON object")
    return data


def parse_instant(value: str, field: str) -> dt.datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        instant = dt.datetime.fromisoformat(normalized)
    except Exception as exc:
        raise SemanticControlError(f"{field} must be ISO-8601 datetime") from exc
    if instant.tzinfo is None:
        raise SemanticControlError(f"{field} must include timezone")
    return instant.astimezone(dt.timezone.utc)


def canonical_profile_for_hash(profile: dict[str, Any]) -> dict[str, Any]:
    canonical = copy.deepcopy(profile)
    metadata = canonical.get("metadata") or {}
    metadata.pop("profileSha256", None)
    metadata.pop("signatureRef", None)
    canonical["metadata"] = metadata
    return canonical


def profile_sha256(profile: dict[str, Any]) -> str:
    canonical = canonical_profile_for_hash(profile)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SemanticControlError(message)


def validate_shape(profile: dict[str, Any]) -> None:
    require(profile.get("apiVersion") == "sct.socioprophet.org/v0.1", "apiVersion must be sct.socioprophet.org/v0.1")
    require(profile.get("kind") == "SCTControlProfile", "kind must be SCTControlProfile")
    metadata = profile.get("metadata")
    spec = profile.get("spec")
    require(isinstance(metadata, dict), "metadata must be an object")
    require(isinstance(spec, dict), "spec must be an object")

    for field in ("name", "version", "issuedAt", "expiresAt", "issuer", "audience", "profileSha256", "keyId", "signatureRef"):
        require(field in metadata, f"metadata.{field} is required")
    require(isinstance(metadata["audience"], list) and metadata["audience"], "metadata.audience must be a non-empty array")
    require(all(isinstance(x, str) and x for x in metadata["audience"]), "metadata.audience entries must be non-empty strings")
    require(isinstance(metadata["profileSha256"], str) and len(metadata["profileSha256"]) == 64, "metadata.profileSha256 must be sha256 hex")

    for field in ("motifs", "runtimeProjection", "delivery", "deconfliction", "replayPolicy", "failMode"):
        require(field in spec, f"spec.{field} is required")

    motifs = spec["motifs"]
    require(isinstance(motifs, list) and motifs, "spec.motifs must be a non-empty array")
    for index, motif in enumerate(motifs):
        require(isinstance(motif, dict), f"spec.motifs[{index}] must be an object")
        name = motif.get("name")
        require(name in ALLOWED_MOTIFS, f"spec.motifs[{index}].name is not an allowed motif: {name}")
        if "weight" in motif:
            weight = motif["weight"]
            require(isinstance(weight, (int, float)) and 0 <= weight <= 1, f"spec.motifs[{index}].weight must be in [0,1]")

    projection = spec["runtimeProjection"]
    require(isinstance(projection, dict), "spec.runtimeProjection must be an object")
    if "toolBudget" in projection:
        require(isinstance(projection["toolBudget"], int) and projection["toolBudget"] >= 0, "runtimeProjection.toolBudget must be non-negative integer")
    if "plannerBranchBudget" in projection:
        require(isinstance(projection["plannerBranchBudget"], int) and projection["plannerBranchBudget"] >= 0, "runtimeProjection.plannerBranchBudget must be non-negative integer")
    if "maxRunSeconds" in projection:
        require(isinstance(projection["maxRunSeconds"], int) and 5 <= projection["maxRunSeconds"] <= 3600, "runtimeProjection.maxRunSeconds must be in [5,3600]")
    if "memoryScope" in projection:
        require(projection["memoryScope"] in ALLOWED_MEMORY_SCOPES, "runtimeProjection.memoryScope invalid")
    if "disclosureScope" in projection:
        require(projection["disclosureScope"] in ALLOWED_DISCLOSURE_SCOPES, "runtimeProjection.disclosureScope invalid")
    if "auditMode" in projection:
        require(projection["auditMode"] in ALLOWED_AUDIT_MODES, "runtimeProjection.auditMode invalid")

    delivery = spec["delivery"]
    require(isinstance(delivery, dict), "spec.delivery must be an object")
    require(delivery.get("mode") in ALLOWED_DELIVERY, "spec.delivery.mode invalid")
    require(delivery.get("failClosed") is True, "spec.delivery.failClosed must be true")
    require(isinstance(delivery.get("authorizedAudience"), list) and delivery["authorizedAudience"], "spec.delivery.authorizedAudience must be non-empty array")

    deconfliction = spec["deconfliction"]
    require(isinstance(deconfliction, dict), "spec.deconfliction must be an object")
    replay = spec["replayPolicy"]
    require(isinstance(replay, dict), "spec.replayPolicy must be an object")
    require(spec.get("failMode") in ALLOWED_FAIL_MODES, "spec.failMode invalid")


def validate_profile(
    profile: dict[str, Any],
    *,
    audience: str | None = None,
    revoked_keys: set[str] | None = None,
    now: dt.datetime | None = None,
    check_hash: bool = True,
) -> dict[str, Any]:
    validate_shape(profile)
    revoked_keys = revoked_keys or set()
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    metadata = profile["metadata"]
    spec = profile["spec"]

    issued_at = parse_instant(metadata["issuedAt"], "metadata.issuedAt")
    expires_at = parse_instant(metadata["expiresAt"], "metadata.expiresAt")
    require(issued_at <= now, "profile not yet valid")
    require(now < expires_at, "profile expired")
    require(metadata["keyId"] not in revoked_keys, "profile signing key is revoked")

    if audience is not None:
        require(audience in metadata["audience"], "requested audience not in metadata.audience")
        require(audience in spec["delivery"]["authorizedAudience"], "requested audience not in delivery.authorizedAudience")

    if check_hash:
        expected = profile_sha256(profile)
        require(metadata["profileSha256"].lower() == expected, "metadata.profileSha256 does not match canonical profile hash")

    motif_names = {m["name"] for m in spec["motifs"]}
    projection = spec["runtimeProjection"]
    deconfliction = spec["deconfliction"]

    if "chapel" in motif_names:
        require(projection.get("memoryScope") in {"none", "local-only"}, "chapel motif cannot project to exportable memory scope")
    if "neck" in motif_names:
        require(projection.get("toolBudget", 0) <= 5, "neck motif must not expand toolBudget above 5")
        require(projection.get("disclosureScope", "minimal") in {"minimal", "bounded"}, "neck motif must not expand disclosureScope")
    if "fork" in motif_names:
        require(projection.get("plannerBranchBudget", 0) <= 8, "fork motif plannerBranchBudget must be bounded at <= 8")
    if "river" in motif_names or "channel" in motif_names:
        require(projection.get("maxRunSeconds", 5) <= 3600, "river/channel motif maxRunSeconds must remain bounded")
    if "rupture" in motif_names:
        require(projection.get("humanGateRequired") is True, "rupture motif requires humanGateRequired projection")
        require(deconfliction.get("breakGlassReasonRequired") is True, "rupture motif requires breakGlassReasonRequired")

    return {
        "profileRef": metadata["name"],
        "profileHash": metadata["profileSha256"].lower(),
        "profileKeyId": metadata["keyId"],
        "profileAudience": metadata["audience"],
        "projection": projection,
        "motifs": sorted(motif_names),
    }


def check_replay(previous: dict[str, Any], next_profile: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    prev = validate_profile(previous, **kwargs)
    nxt = validate_profile(next_profile, **kwargs)
    if prev["profileHash"] == nxt["profileHash"]:
        return {"result": "allow", "reason": "same profile hash", "profileHash": nxt["profileHash"]}

    replay = next_profile["spec"].get("replayPolicy") or {}
    if replay.get("allowAuthorizedSuccessor") is True:
        require(replay.get("authorizedSuccessorOf") == prev["profileHash"], "authorized successor does not reference previous profile hash")
        require(isinstance(replay.get("successorSignatureRef"), str) and replay["successorSignatureRef"], "authorized successor requires successorSignatureRef")
        return {"result": "allow", "reason": "signed authorized successor", "profileHash": nxt["profileHash"], "successorOf": prev["profileHash"]}

    raise SemanticControlError("replay semantic drift denied: profile hash changed without authorized successor")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SEM-K SCTControlProfile contracts")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_profile = sub.add_parser("profile", help="validate one SCTControlProfile")
    p_profile.add_argument("path")
    p_profile.add_argument("--audience")
    p_profile.add_argument("--revoked-key", action="append", default=[])
    p_profile.add_argument("--now")
    p_profile.add_argument("--skip-hash", action="store_true")

    p_replay = sub.add_parser("replay", help="validate replay profile continuity")
    p_replay.add_argument("previous")
    p_replay.add_argument("next")
    p_replay.add_argument("--audience")
    p_replay.add_argument("--revoked-key", action="append", default=[])
    p_replay.add_argument("--now")
    p_replay.add_argument("--skip-hash", action="store_true")

    args = parser.parse_args()
    now = parse_instant(args.now, "--now") if getattr(args, "now", None) else None
    kwargs = {
        "audience": getattr(args, "audience", None),
        "revoked_keys": set(getattr(args, "revoked_key", []) or []),
        "now": now,
        "check_hash": not getattr(args, "skip_hash", False),
    }

    try:
        if args.cmd == "profile":
            result = validate_profile(load_json(Path(args.path)), **kwargs)
        else:
            result = check_replay(load_json(Path(args.previous)), load_json(Path(args.next)), **kwargs)
    except SemanticControlError as exc:
        print(f"[semantic-control] DENY: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({"result": "allow", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
