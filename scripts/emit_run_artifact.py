#!/usr/bin/env python3
"""Emit a RunArtifact into the bundle artifacts directory.

This is the downstream evidence layer that complements:
- scripts/validate_bundle.py -> validation-artifact.json
- scripts/select-executor.py -> PlacementDecision (stdout)

Usage:
  scripts/emit_run_artifact.py <bundle.json> <executor-name> <exit-code> [--stdout <path>] [--stderr <path>]

Notes:
- This script does not execute the bundle. It records the outcome of a run performed by a runner backend.
- Upstream workspace artifacts (from sociosphere) may be referenced via optional env vars.
- SourceOS delegated execution refs (Tekton/Katello/digests/smoke receipts) may be referenced via optional env vars.
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
    print(f"[run-artifact] ERROR: {msg}", file=sys.stderr)
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
    """Collect declared and delegated SourceOS image-production evidence refs.

    Declared refs come from the Bundle. Delegated refs come from the execution
    environment and represent external systems Agentplane may invoke or observe,
    such as Tekton and Katello. Secrets must remain refs only and are not copied.
    """
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

    # Preserve bundle-declared output refs as defaults when the execution
    # environment did not provide a stronger delegated runtime ref.
    for field in ("katelloContentRef", "ostreeRef", "releaseSetRef", "bootReleaseSetRef", "smokeReceiptRef"):
        if field not in delegated and _non_empty(outputs.get(field)):
            delegated[field] = outputs[field]

    return {
        "enabled": enabled,
        "declared": declared,
        "delegatedExecution": delegated,
    }


def main() -> int:
    ap = argparse.ArgumentParser(prog="emit_run_artifact")
    ap.add_argument("bundle", help="path to bundle.json")
    ap.add_argument("executor", help="chosen executor name")
    ap.add_argument("exit_code", type=int, help="exit code from the run")
    ap.add_argument("--stdout", dest="stdout_ref", default=None)
    ap.add_argument("--stderr", dest="stderr_ref", default=None)
    ap.add_argument("--bundle-path", dest="bundle_path", default=None)
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

    lane = (spec.get("policy") or {}).get("lane")
    backend = ((spec.get("vm") or {}).get("backendIntent"))
    if not lane or not backend:
        die("bundle spec.policy.lane and spec.vm.backendIntent are required", 2)

    status = "success" if args.exit_code == 0 else "failure"

    upstream = {
        "workspaceInventoryRef": os.getenv("SOCIOSPHERE_WORKSPACE_INVENTORY_REF"),
        "lockVerificationRef": os.getenv("SOCIOSPHERE_LOCK_VERIFICATION_REF"),
        "protocolCompatibilityRef": os.getenv("SOCIOSPHERE_PROTOCOL_COMPATIBILITY_REF"),
        "taskRunRefs": [p for p in (os.getenv("SOCIOSPHERE_TASK_RUN_REFS") or "").split(",") if p],
    }

    artifact = {
        "kind": "RunArtifact",
        "bundle": f"{name}@{ver}",
        "bundlePath": args.bundle_path,
        "capturedAt": now_iso(),
        "lane": lane,
        "executor": args.executor,
        "backendIntent": backend,
        "status": status,
        "exitCode": int(args.exit_code),
        "stdoutRef": args.stdout_ref,
        "stderrRef": args.stderr_ref,
        "upstreamArtifacts": upstream,
        "sourceosBindings": extract_sourceos_bindings(spec),
        "sourceosImageProduction": extract_sourceos_image_production(spec),
    }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "run-artifact.json"
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[run-artifact] OK: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
