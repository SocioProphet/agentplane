#!/usr/bin/env python3
"""SourceOS delegated execution runner.

This runner is the Agentplane bridge from a SourceOS image-production Bundle to
external SourceOS/SociOS automation surfaces such as Tekton and Katello.

It is intentionally safe by default:
- validates the bundle first;
- renders an execution request artifact;
- records delegated execution refs supplied by arguments or environment;
- emits Agentplane RunArtifact and ReplayArtifact;
- defaults to record-only mode;
- fails closed for submit mode unless side effects and credential refs are explicit;
- only executes live kubectl calls when --execute-live is explicit;
- does not inline secrets.

Modes:
- record-only: render and emit evidence only. No external mutation.
- tekton-observe: record or observe an existing Tekton PipelineRun/TaskRun surface.
- tekton-submit: guarded submit intent. Requires explicit side-effect permission
  and credential refs. Live submission additionally requires --execute-live,
  a manifest, and a kubeconfig environment binding.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
VALID_MODES = {"record-only", "tekton-observe", "tekton-submit"}


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


def run_capture(cmd: list[str], env: dict[str, str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )


def merge_env(base: dict[str, str], updates: dict[str, str | None]) -> dict[str, str]:
    env = dict(base)
    for key, value in updates.items():
        if value not in (None, ""):
            env[key] = str(value)
    return env


def split_csv(values: list[str]) -> str:
    return ",".join([value.strip() for value in values if value.strip()])


def require_non_empty(value: str | None, name: str) -> None:
    if value in (None, ""):
        die(f"{name} is required", 2)


def credential_env(args: argparse.Namespace) -> dict[str, str]:
    if not args.kubeconfig_env:
        die("--kubeconfig-env is required for live Tekton modes", 2)
    kubeconfig_value = os.getenv(args.kubeconfig_env)
    if not kubeconfig_value:
        die(f"environment variable {args.kubeconfig_env} must be set for live Tekton modes", 2)
    return {"KUBECONFIG": kubeconfig_value}


def validate_live_adapter(args: argparse.Namespace) -> None:
    if not args.execute_live:
        return
    if args.mode == "record-only":
        die("--execute-live is not valid with record-only mode", 2)
    if not shutil.which(args.kubectl_bin):
        die(f"kubectl binary not found: {args.kubectl_bin}", 2)
    require_non_empty(args.kubeconfig_ref, "--kubeconfig-ref is required for live Tekton modes")
    require_non_empty(args.kubeconfig_env, "--kubeconfig-env is required for live Tekton modes")
    credential_env(args)
    if args.mode == "tekton-observe":
        require_non_empty(args.pipeline_run_name, "--pipeline-run-name is required for live tekton-observe")
        require_non_empty(args.tekton_namespace, "--tekton-namespace is required for live tekton-observe")
    if args.mode == "tekton-submit":
        require_non_empty(args.pipeline_run_manifest, "--pipeline-run-manifest is required for live tekton-submit")
        manifest = Path(args.pipeline_run_manifest)
        if not manifest.exists():
            die(f"pipeline run manifest not found: {manifest}", 2)


def validate_mode(args: argparse.Namespace, bundle: dict[str, Any]) -> dict[str, Any]:
    if args.mode not in VALID_MODES:
        die(f"--mode must be one of {sorted(VALID_MODES)}", 2)

    spec = bundle.get("spec") or {}
    secrets = spec.get("secrets") or {}
    required_secret_refs = secrets.get("required") or []
    if any(not isinstance(ref, str) or not ref.strip() for ref in required_secret_refs):
        die("spec.secrets.required must contain non-empty secret reference names", 2)

    mode_gate = {
        "mode": args.mode,
        "sideEffectsAllowed": bool(args.allow_side_effects),
        "executeLiveRequested": bool(args.execute_live),
        "liveExternalMutationPerformed": False,
        "credentialRefsOnly": True,
        "requiredSecretRefs": required_secret_refs,
    }

    if args.mode == "tekton-observe":
        if not args.execute_live:
            require_non_empty(args.pipeline_run_ref, "--pipeline-run-ref is required for tekton-observe mode")
        mode_gate["requirement"] = "observe_existing_pipeline_run"
        validate_live_adapter(args)
        return mode_gate

    if args.mode == "tekton-submit":
        if not args.allow_side_effects:
            die("tekton-submit requires --allow-side-effects", 2)
        require_non_empty(args.tekton_namespace, "--tekton-namespace is required for tekton-submit mode")
        require_non_empty(args.tekton_pipeline_name, "--tekton-pipeline-name is required for tekton-submit mode")
        require_non_empty(args.kubeconfig_ref, "--kubeconfig-ref is required for tekton-submit mode")
        require_non_empty(args.tekton_service_account_ref, "--tekton-service-account-ref is required for tekton-submit mode")
        if not required_secret_refs:
            die("tekton-submit requires spec.secrets.required credential references", 2)
        mode_gate["requirement"] = "guarded_submit_intent"
        mode_gate["tektonNamespace"] = args.tekton_namespace
        mode_gate["tektonPipelineName"] = args.tekton_pipeline_name
        mode_gate["kubeconfigRef"] = args.kubeconfig_ref
        mode_gate["tektonServiceAccountRef"] = args.tekton_service_account_ref
        mode_gate["submitImplementation"] = "live_kubectl_apply" if args.execute_live else "recorded_intent_only"
        validate_live_adapter(args)
        return mode_gate

    validate_live_adapter(args)
    mode_gate["requirement"] = "record_only"
    return mode_gate


def run_live_adapter(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    if not args.execute_live:
        return {
            "requested": False,
            "performed": False,
            "result": "not_requested",
        }

    live_dir = out_dir / "live-tekton"
    live_dir.mkdir(parents=True, exist_ok=True)
    env = merge_env(os.environ, credential_env(args))

    if args.mode == "tekton-observe":
        cmd = [
            args.kubectl_bin,
            "get",
            "pipelinerun",
            args.pipeline_run_name,
            "-n",
            args.tekton_namespace,
            "-o",
            "json",
        ]
        command_kind = "kubectl_get_pipelinerun"
    elif args.mode == "tekton-submit":
        cmd = [
            args.kubectl_bin,
            "apply",
            "-n",
            args.tekton_namespace,
            "-f",
            args.pipeline_run_manifest,
        ]
        command_kind = "kubectl_apply_pipelinerun"
    else:
        die(f"unsupported live mode: {args.mode}", 2)

    started = now_iso()
    try:
        completed = run_capture(cmd, env, args.live_timeout_seconds)
        exit_code = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or "" if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr or "" if isinstance(exc.stderr, str) else ""
        stderr += f"\nTimed out after {args.live_timeout_seconds}s"

    stdout_path = live_dir / f"{command_kind}.stdout.txt"
    stderr_path = live_dir / f"{command_kind}.stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    observed_ref = args.pipeline_run_ref
    if args.mode == "tekton-observe" and args.pipeline_run_name:
        observed_ref = args.pipeline_run_ref or f"tekton://pipelinerun/{args.tekton_namespace}/{args.pipeline_run_name}"
    elif args.mode == "tekton-submit":
        observed_ref = args.pipeline_run_ref or f"tekton://pipelinerun/{args.tekton_namespace}/{Path(args.pipeline_run_manifest).stem}"

    result = {
        "requested": True,
        "performed": exit_code == 0,
        "result": "success" if exit_code == 0 else "failure",
        "mode": args.mode,
        "commandKind": command_kind,
        "command": {
            "argv": cmd,
            "redacted": False,
        },
        "startedAt": started,
        "completedAt": now_iso(),
        "exitCode": exit_code,
        "stdoutRef": str(stdout_path),
        "stderrRef": str(stderr_path),
        "pipelineRunRef": observed_ref,
        "kubeconfigRef": args.kubeconfig_ref,
        "kubeconfigEnv": args.kubeconfig_env,
    }
    write_json(live_dir / "live-tekton-result.json", result)
    if exit_code != 0:
        die(f"live Tekton adapter failed with exit code {exit_code}; see {stderr_path}", exit_code)
    return result


def render_execution_request(
    bundle: dict[str, Any],
    bundle_path: Path,
    args: argparse.Namespace,
    mode_gate: dict[str, Any],
    live_result: dict[str, Any],
) -> dict[str, Any]:
    spec = bundle.get("spec") or {}
    sourceos = spec.get("sourceos") or {}
    automation = spec.get("sociosAutomation") or {}
    outputs = spec.get("outputs") or {}
    policy = spec.get("policy") or {}
    secrets = spec.get("secrets") or {}

    non_goals = [
        "does not publish to Katello",
        "does not inline secrets",
    ]
    if args.mode == "record-only":
        non_goals.extend([
            "does not invoke Tekton directly",
            "does not mutate host state",
        ])
    if args.mode == "tekton-observe" and not args.execute_live:
        non_goals.extend([
            "does not invoke Tekton directly",
            "does not mutate host state",
        ])
    if args.mode == "tekton-submit" and not args.execute_live:
        non_goals.extend([
            "does not invoke Tekton directly in this invocation",
            "records guarded submit intent only",
        ])

    delegated_pipeline_ref = args.pipeline_run_ref or live_result.get("pipelineRunRef")

    return {
        "kind": "SourceOSDelegatedExecutionRequest",
        "apiVersion": "agentplane.socioprophet.org/v0.1",
        "bundle": bundle_name(bundle),
        "bundlePath": str(bundle_path),
        "createdAt": now_iso(),
        "mode": args.mode,
        "modeGate": mode_gate,
        "liveTekton": live_result,
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
            "tektonPipelineRunRef": delegated_pipeline_ref,
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
        "submitIntent": {
            "tektonNamespace": args.tekton_namespace,
            "tektonPipelineName": args.tekton_pipeline_name,
            "pipelineRunManifest": args.pipeline_run_manifest,
            "kubeconfigRef": args.kubeconfig_ref,
            "tektonServiceAccountRef": args.tekton_service_account_ref,
        } if args.mode == "tekton-submit" else None,
        "secretRefs": {
            "secretRefRoot": secrets.get("secretRefRoot"),
            "required": secrets.get("required") or [],
        },
        "nonGoals": non_goals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Record SourceOS delegated execution evidence.")
    parser.add_argument("bundle", help="Path to Agentplane bundle.json")
    parser.add_argument("--mode", choices=sorted(VALID_MODES), default="record-only")
    parser.add_argument("--allow-side-effects", action="store_true")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--executor", default="sourceos-delegated-record", help="Executor name to record in artifacts")
    parser.add_argument("--pipeline-run-ref", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_RUN_REF"))
    parser.add_argument("--pipeline-run-name", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_RUN_NAME"))
    parser.add_argument("--pipeline-run-manifest", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_RUN_MANIFEST"))
    parser.add_argument("--task-run-ref", action="append", default=[])
    parser.add_argument("--tekton-namespace", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_NAMESPACE"))
    parser.add_argument("--tekton-pipeline-name", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_PIPELINE_NAME"))
    parser.add_argument("--tekton-service-account-ref", default=os.getenv("AGENTPLANE_SOURCEOS_TEKTON_SERVICE_ACCOUNT_REF"))
    parser.add_argument("--kubeconfig-ref", default=os.getenv("AGENTPLANE_SOURCEOS_KUBECONFIG_REF"))
    parser.add_argument("--kubeconfig-env", default=os.getenv("AGENTPLANE_SOURCEOS_KUBECONFIG_ENV", "KUBECONFIG"))
    parser.add_argument("--kubectl-bin", default=os.getenv("AGENTPLANE_SOURCEOS_KUBECTL_BIN", "kubectl"))
    parser.add_argument("--live-timeout-seconds", type=int, default=int(os.getenv("AGENTPLANE_SOURCEOS_LIVE_TIMEOUT_SECONDS", "120")))
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
    mode_gate = validate_mode(args, bundle)
    live_result = run_live_adapter(args, out_dir)
    if live_result.get("pipelineRunRef") and not args.pipeline_run_ref:
        args.pipeline_run_ref = live_result["pipelineRunRef"]
    if args.execute_live:
        mode_gate["liveExternalMutationPerformed"] = bool(live_result.get("performed") and args.mode == "tekton-submit")
        mode_gate["liveResult"] = live_result.get("result")

    request = render_execution_request(bundle, bundle_path, args, mode_gate, live_result)
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
