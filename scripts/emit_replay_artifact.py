#!/usr/bin/env python3
"""Emit a ReplayArtifact into the bundle artifacts directory.

Usage:
  scripts/emit_replay_artifact.py <bundle.json> <executor-name> [--bundle-rev <sha>] [--bundle-path <path>]

This artifact records the minimum inputs needed to replay a run deterministically:
- bundle path + rev (when available)
- artifact directory
- policy pack refs/hashes
- required secret refs (names only)
- optional upstream workspace artifact references
- SourceOS delegated execution references when the bundle uses that lane
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

SOURCEOS_BINDING_KEYS = {
    "contentSpecRef",
    "overlayRefs",
    "buildRequestRef",
    "releaseManifestRef",
    "enrollmentProfileRef",
    "evidenceBundleRef",
    "localExecutionProtocolRef",
    "remoteExecutionProtocolRef",
}

SOURCEOS_ENV_KEYS = {
    "tektonPipelineRunRef": "AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_RUN_REF",
    "tektonTaskRunRefs": "AGENTPLANE_SOURCEOS_TEKTON_TASK_RUN_REFS",
    "katelloContentRef": "AGENTPLANE_SOURCEOS_KATELLO_CONTENT_REF",
    "katelloContentViewRef": "AGENTPLANE_SOURCEOS_KATELLO_CONTENT_VIEW_REF",
    "katelloLifecycleEnvironmentRef": "AGENTPLANE_SOURCEOS_KATELLO_LIFECYCLE_ENVIRONMENT_REF",
    "outputArtifactRef": "AGENTPLANE_SOURCEOS_OUTPUT_ARTIFACT_REF",
    "outputDigest": "AGENTPLANE_SOURCEOS_OUTPUT_DIGEST",
    "ostreeRef": "AGENTPLANE_SOURCEOS_OSTREE_REF",
    "releaseSetRef": "AGENTPLANE_SOURCEOS_RELEASE_SET_REF",
    "bootReleaseSetRef": "AGENTPLANE_SOURCEOS_BOOT_RELEASE_SET_REF",
    "smokeReceiptRef": "AGENTPLANE_SOURCEOS_SMOKE_RECEIPT_REF",
}


def die(msg: str, code: int = 2) -> None:
    print(f"[replay-artifact] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_bundle(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"invalid bundle json: {e}", 2)


def _non_empty(value: Any) -> bool:
    return value not in (None, "", [])


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _split_env_list(name: str) -> list[str]:
    raw = os.getenv(name) or ""
    return [part.strip() for part in raw.split(",") if part.strip()]


def _copy_non_empty(source: dict[str, Any], keys: list[str] | tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in keys:
        value = source.get(key)
        if _non_empty(value):
            out[key] = value
    return out


def extract_sourceos_bindings(spec: dict[str, Any]) -> dict[str, Any]:
    integration_refs = spec.get("integrationRefs") or {}
    sourceos = integration_refs.get("sourceos") or spec.get("sourceosBuildRelease") or {}
    if not isinstance(sourceos, dict):
        return {}

    out: dict[str, Any] = {}
    for key in SOURCEOS_BINDING_KEYS:
        value = sourceos.get(key)
        if _non_empty(value):
            out[key] = value
    return out


def extract_sourceos_image_production(spec: dict[str, Any]) -> dict[str, Any]:
    sourceos = spec.get("sourceos") if isinstance(spec.get("sourceos"), dict) else {}
    automation = spec.get("sociosAutomation") if isinstance(spec.get("sociosAutomation"), dict) else {}
    outputs = spec.get("outputs") if isinstance(spec.get("outputs"), dict) else {}

    enabled = bool(sourceos or automation or outputs)

    declared = {
        "sourceos": _copy_non_empty(
            sourceos,
            (
                "artifactTruthRef",
                "flavorRef",
                "installerProfileRef",
                "channelRef",
                "manifestRef",
                "sourceosSpecRef",
                "cosaRef",
                "butaneRefs",
                "releaseSetRef",
                "bootReleaseSetRef",
            ),
        ),
        "sociosAutomation": _copy_non_empty(
            automation,
            (
                "substrateDocRef",
                "katelloContentModelRef",
                "tektonPipelineRef",
                "tektonTaskRefs",
                "katelloProduct",
                "katelloRepository",
                "katelloContentView",
                "katelloLifecycleEnvironment",
                "smartProxyRef",
                "argocdApplicationRef",
            ),
        ),
        "outputs": _copy_non_empty(
            outputs,
            (
                "releaseSetRef",
                "bootReleaseSetRef",
                "evidenceBundleRef",
                "katelloContentRef",
                "ostreeRef",
                "smokeReceiptRef",
            ),
        ),
    }

    delegated: dict[str, Any] = {}
    for field, env_name in SOURCEOS_ENV_KEYS.items():
        if field == "tektonTaskRunRefs":
            value = _split_env_list(env_name)
        else:
            value = _string_or_none(os.getenv(env_name))
        if _non_empty(value):
            delegated[field] = value

    for field in ("katelloContentRef", "ostreeRef", "releaseSetRef", "bootReleaseSetRef", "smokeReceiptRef"):
        if field not in delegated and _non_empty(outputs.get(field)):
            delegated[field] = outputs[field]

    return {
        "enabled": enabled,
        "declared": declared,
        "delegatedExecution": delegated,
    }


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_replay_artifact")
    ap.add_argument("bundle", help="path to bundle.json")
    ap.add_argument("executor", help="chosen executor name")
    ap.add_argument("--bundle-rev", default=None)
    ap.add_argument("--bundle-path", default=None)
    args = ap.parse_args()

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        die(f"bundle not found: {bundle_path}", 2)

    b = load_bundle(bundle_path)
    md = b.get("metadata") or {}
    spec = b.get("spec") or {}

    name = md.get("name")
    ver = md.get("version")
    if not name or not ver:
        die("bundle metadata.name and metadata.version are required", 2)

    out_dir = (spec.get("artifacts") or {}).get("outDir")
    if not out_dir:
        die("bundle spec.artifacts.outDir is required", 2)

    backend = ((spec.get("vm") or {}).get("backendIntent"))
    if not backend:
        die("bundle spec.vm.backendIntent is required", 2)

    pol = spec.get("policy") or {}
    secrets = spec.get("secrets") or {}

    upstream = {
        "workspaceInventoryRef": os.getenv("SOCIOSPHERE_WORKSPACE_INVENTORY_REF"),
        "lockVerificationRef": os.getenv("SOCIOSPHERE_LOCK_VERIFICATION_REF"),
        "protocolCompatibilityRef": os.getenv("SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF"),
        "taskRunRefs": [p for p in (os.getenv("SOCIOSPHERE_TASK_RUN_REFS") or "").split(",") if p],
    }

    artifact = {
        "kind": "ReplayArtifact",
        "bundle": f"{name}@{ver}",
        "capturedAt": now_iso(),
        "executor": args.executor,
        "backendIntent": backend,
        "inputs": {
            "bundlePath": args.bundle_path or str(bundle_path),
            "bundleRev": args.bundle_rev,
            "artifactDir": str(Path(out_dir).resolve()),
            "policyPackRef": pol.get("policyPackRef"),
            "policyPackHash": pol.get("policyPackHash"),
            "secretsRequired": secrets.get("required") or [],
            "upstreamArtifacts": upstream,
            "sourceosBindings": extract_sourceos_bindings(spec),
            "sourceosImageProduction": extract_sourceos_image_production(spec),
        },
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "replay-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[replay-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
