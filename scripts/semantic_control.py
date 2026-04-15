#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


class SemanticControlError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_profile_bytes(profile: dict[str, Any]) -> bytes:
    normalized = json.loads(json.dumps(profile))
    metadata = normalized.get("metadata") or {}
    metadata.pop("profileSha256", None)
    normalized["metadata"] = metadata
    return json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")


def profile_sha256(profile: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_profile_bytes(profile)).hexdigest()


def resolve_profile_path(profile_ref: str, bundle_path: Path) -> Path:
    ref = Path(profile_ref)
    return ref if ref.is_absolute() else (bundle_path.parent / ref).resolve()


def verify_expiry(profile: dict[str, Any]) -> tuple[bool, str]:
    metadata = profile.get("metadata") or {}
    issued = dt.datetime.fromisoformat(str(metadata.get("issuedAt", "1970-01-01T00:00:00+00:00")).replace("Z", "+00:00"))
    expires = dt.datetime.fromisoformat(str(metadata.get("expiresAt", "1970-01-01T00:00:00+00:00")).replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    if now < issued:
        return False, "not yet valid"
    if now >= expires:
        return False, "expired"
    return True, "valid"


def derive_projection(profile: dict[str, Any], semantic_control: dict[str, Any] | None = None) -> dict[str, Any]:
    base = dict((profile.get("spec") or {}).get("runtimeProjection") or {})
    override = dict((semantic_control or {}).get("projectionOverride") or {})
    return {**base, **override}
