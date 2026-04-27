#!/usr/bin/env python3
"""SourceOS delegated execution runner.

This runner is the Agentplane bridge from a SourceOS image-production Bundle to
external SourceOS/SociOS automation surfaces such as Tekton and Katello.

It is intentionally safe by default:
- validates the bundle first;
- renders an execution request artifact;
- records delegated execution refs supplied by arguments or environment;
- emits Agentplane RunArtifact and ReplayArtifact;
- does not mutate a cluster, invoke Tekton, or publish to Katello unless a future
  runner backend explicitly implements that behavior.

Usage:
  scripts/run_sourceos_delegated.py bundles/sourceos-image-production-smoke/bundle.json \
    --executor ci-sourceos-delegated \
    --pipeline-run-ref tekton://sourceos-customize-live-iso/pr-smoke \
    --task-run-ref tekton://task/customize-live-iso \
    --task-run-ref tekton://task/publish-katello-file-repo \
    --katello-content-ref katello://SourceOS/SourceOS-Recovery/sourceos-live.iso@ci-smoke \
    --output-digest sha256:UNSET-CI-SMOKE
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


def die(message: str, code: int = 2) -> None:
    print(f"[sourceos-delegated] ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"invalid JSON at {path}: {exc}", 2)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bundle_name(bundle: dict[str, Any]) -> str:
    metadata = bundle.get("metadata") or {}
    name = metadata.get("name")
    version = metadata.get("version")
    if not name or not version:
        die("bundle metadata.name and metadata.version are required", 2)
    return f"{name}@{version}"


def artifact_dir(bundle: dict[str, Any]) -> Path:
    out_dir = ((bundle.get("spec") or {}).get("artifacts") or {}).get("outDir")
    if not out_dir:
        die("bundle spec.artifacts.outDir is required", 2)
    return Path(out_dir)


def require_sourceos_lane(bundle: dict[str, Any]) -> None:
    spec = bundle.get("spec") or {}
    missing = []
    for field in ("sourceos", "sociosAutomation"):
        if not isinstance(spec.get(field), dict) or not spec.get(field):
            missing.append(f"spec.{field}")
    if missing:
        die("SourceOS delegated execution requires " + ", ".join(missing), 2)


def run_checked(cmd: list[str], env: dict[str, str] | None = None) -> None:
    result = subprocess.run(cmd, cwd=REPO_ROOT, env=env, text=True)
    if result.returncode != 0:
        die(f"command failed ({result.returncode}): {' '.join(cmd)}", result.returncode)


def merge_env(base: dict[str, str], updates: dict[str, str | None]) -> dict[str, str]:
    env = dict(base)
    for key, value in updates.items():
        if value not in (None, ""):
            env[key] = str(value)
    return env


def split_csv(values: list[str]) -> str:
    return ",".join([value.strip() for value in values if value.strip()])


def render_execution_request(
    bundle: dict[str, Any],
    bundle_path: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    spec = bundle.get("spec") or {}
    sourceos = spec.get("sourceos") or {}
    automation = spec.get("sociosAutomation") or {}
    outputs = spec.get("outputs") or {}
    policy = spec.get("policy") or {}
    secrets = spec.get("secrets") or {}

    return {
        "kind": "SourceOSDelegatedExecutionRequest",
        "apiVersion": "agentplane.socioprophet.org/v0.1",
        "bundle": bundle_name(bundle),
        "bundlePath": str(bundle_path),
        "createdAt": now_iso(),
        "mode": "record-only",
        "executor": args.executor,
        "policy": {
            "lane": policy.get("lane"),
            "policyPackRef": policy.get("policyPackRef"),
            "policyPackHash": policy.get("policyPackHash"),
            "humanGateRequired": policy.get("humanGateRequired"),
        },
        "sourceos": sourceos,
        "sociosAutomation": automation,
        "declaredOutputs": outputs,
        "delegatedExecution": {
            "tektonPipelineRunRef": args.pipeline_run_ref,
            "tektonTaskRunRefs": args.task_run_ref,
            "katelloContentRef": args.katello_content_ref,
            "katelloContentViewRef": args.katello_content_view_ref,
            "katelloLifecycleEnvironmentRef": args.katello_lifecycle_environment_ref,
            "outputArtifactRef": args.output_artifact_ref,
            "outputDigest": args.output_digest,
            "ostreeRef": args.ostree_ref,
            "releaseSetRef": args.release_set_ref,
            "bootReleaseSetRef": args.boot_release_set_ref,
            "smokeReceiptRef": args.smoke_receipt_ref,
        },
        "secretRefs": {
            "secretRefRoot": secrets.get("secretRefRoot"),
            "required": secrets.get("required") or [],
        },
        "nonGoals": [
            "does not invoke Tekton directly",
            "does not publish to Katello",
            "does not mutate host state",
            "does not inline secrets",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Record SourceOS delegated execution evidence.")
    parser.add_argument("bundle", help="Path to Agentplane bundle.json")
    parser.add_argument("--executor", default="sourceos-delegated-record", help="Executor name to record in artifacts")
    parser.add_argument("--pipeline-run-ref", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_RUN_REF"))
    parser.add_argument("--task-run-ref", action="append", default=[])
    parser.add_argument("--katello-content-ref", default=os.getenv("AGENTPLANE_SOURCEOS_KATELLO_CONTENT_REF"))
    parser.add_argument("--katello-content-view-ref", default=os.getenv("AGENTPLANE_SOURCEOS_KATELLO_CONTENT_VIEW_REF"))
    parser.add_argument("--katello-lifecycle-environment-ref", default=os.getenv("AGENTPLANE_SOURCEOS_KATELLO_LIFECYCLE_ENVIRONMENT_REF"))
    parser.add_argument("--output-artifact-ref", default=os.getenv("AGENTPLANE_SOURCEOS_OUTPUT_ARTIFACT_REF"))
    parser.add_argument("--output-digest", default=os.getenv("AGENTPLANE_SOURCEOS_OUTPUT_DIGEST"))
    parser.add_argument("--ostree-ref", default=os.getenv("AGENTPLANE_SOURCEOS_OSTREE_REF"))
    parser.add_argument("--release-set-ref", default=os.getenv("AGENTPLANE_SOURCEOS_RELEASE_SET_REF"))
    parser.add_argument("--boot-release-set-ref", default=os.getenv("AGENTPLANE_SOURCEOS_BOOT_RELEASE_SET_REF"))
    parser.add_argument("--smoke-receipt-ref", default=os.getenv("AGENTPLANE_SOURCEOS_SMOKE_RECEIPT_REF"))
    parser.add_argument("--bundle-rev", default=os.getenv("GITHUB_SHA"))
    parser.add_argument("--exit-code", type=int, default=0)
    args = parser.parse_args()

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        die(f"bundle not found: {bundle_path}", 2)
    bundle = load_json(bundle_path)
    require_sourceos_lane(bundle)
    out_dir = artifact_dir(bundle)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_checked([sys.executable, "scripts/validate_bundle.py", str(bundle_path)])

    task_run_refs = args.task_run_ref or []
    if not task_run_refs:
        task_run_refs = [value for value in (os.getenv("AGENTPLANE_SOURCEOS_TEKTON_TASK_RUN_REFS") or "").split(",") if value]

    args.task_run_ref = task_run_refs
    request = render_execution_request(bundle, bundle_path, args)
    write_json(out_dir / "sourceos-delegated-execution-request.json", request)

    artifact_env = merge_env(
        os.environ,
        {
            "AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_RUN_REF": args.pipeline_run_ref,
            "AGENTPLANE_SOURCEOS_TEKTON_TASK_RUN_REFS": split_csv(task_run_refs),
            "AGENTPLANE_SOURCEOS_KATELLO_CONTENT_REF": args.katello_content_ref,
            "AGENTPLANE_SOURCEOS_KATELLO_CONTENT_VIEW_REF": args.katello_content_view_ref,
            "AGENTPLANE_SOURCEOS_KATELLO_LIFECYCLE_ENVIRONMENT_REF": args.katello_lifecycle_environment_ref,
            "AGENTPLANE_SOURCEOS_OUTPUT_ARTIFACT_REF": args.output_artifact_ref,
            "AGENTPLANE_SOURCEOS_OUTPUT_DIGEST": args.output_digest,
            "AGENTPLANE_SOURCEOS_OSTREE_REF": args.ostree_ref,
            "AGENTPLANE_SOURCEOS_RELEASE_SET_REF": args.release_set_ref,
            "AGENTPLANE_SOURCEOS_BOOT_RELEASE_SET_REF": args.boot_release_set_ref,
            "AGENTPLANE_SOURCEOS_SMOKE_RECEIPT_REF": args.smoke_receipt_ref,
        },
    )

    run_checked(
        [sys.executable, "scripts/emit_run_artifact.py", str(bundle_path), args.executor, str(args.exit_code)],
        env=artifact_env,
    )
    run_checked(
        [
            sys.executable,
            "scripts/emit_replay_artifact.py",
            str(bundle_path),
            args.executor,
            "--bundle-rev",
            args.bundle_rev or "UNSET",
        ],
        env=artifact_env,
    )

    print(f"[sourceos-delegated] OK: wrote evidence under {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
