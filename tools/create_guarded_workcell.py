#!/usr/bin/env python3
"""Create a guarded AgentPlane workcell under explicit side-effect authority.

This tool is intentionally narrow. It may create a local Git worktree and branch
only when `--allow-side-effects` is present. It never invokes an agent, contacts
model providers, mutates GitHub, pushes branches, or alters CI state.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import plan_guarded_workcell

DEFAULT_PROTECTED_BRANCHES = ("main", "master", "trunk", "prod", "production")
DEFAULT_GUARDRAIL_HOOK_COMMAND = "guardrail-fabric-hook --write-log"
DEFAULT_STOP_GATE_COMMAND = "python3 tools/evaluate_stop_gate.py"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_branch_fragment(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._/-]+", "-", value.strip()).strip("-/.")
    normalized = re.sub(r"/+", "/", normalized)
    return normalized or "workcell"


def default_workspace_path(root: Path, branch: str) -> Path:
    safe = safe_branch_fragment(branch).replace("/", "-")
    return root / ".agentplane" / "workcells" / safe


def run_command(args: list[str], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        return CommandResult(returncode=127, stderr=str(exc))
    return CommandResult(completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def git_value(cwd: Path, args: list[str]) -> str | None:
    result = run_command(["git", *args], cwd)
    if result.returncode != 0:
        return None
    return result.stdout or None


def git_worktree_add(cwd: Path, workspace: Path, branch: str, base_ref: str) -> CommandResult:
    return run_command(["git", "worktree", "add", "-b", branch, str(workspace), base_ref], cwd)


def branch_exists(cwd: Path, branch: str) -> bool:
    return run_command(["git", "rev-parse", "--verify", "--quiet", branch], cwd).returncode == 0


def workspace_exists(workspace: Path) -> bool:
    return workspace.exists()


def build_plan_artifact(
    *,
    args: argparse.Namespace,
    workspace: Path,
    result: str,
    worktree_status: str,
    side_effects: dict[str, bool],
    reason: str | None,
    remediation: str | None,
) -> dict[str, Any]:
    base_commit = args.base_commit or git_value(Path(args.cwd).resolve(), ["rev-parse", args.base_ref])
    remote = args.remote or git_value(Path(args.cwd).resolve(), ["remote", "get-url", "origin"])
    plan = plan_guarded_workcell.WorkcellPlan(
        bundle=args.bundle,
        repo=args.repo,
        base_ref=args.base_ref,
        task_ref=args.task_ref,
        session_ref=args.session_ref,
        branch=args.branch,
        workspace_path=str(workspace),
        strategy=args.strategy,
        runtime_executor=args.runtime_executor,
        runtime_profile_ref=args.runtime_profile_ref,
        environment_ref=args.environment_ref,
        agent_command=args.agent_command,
        guardrail_enabled=not args.no_guardrail,
        guardrail_adapter=args.guardrail_adapter,
        guardrail_hook_command=args.guardrail_hook_command,
        decision_log_ref=args.decision_log_ref,
        policy_pack_ref=args.policy_pack_ref,
        stop_gate_enabled=not args.no_stop_gate,
        stop_gate_artifact_ref=args.stop_gate_artifact_ref,
        stop_gate_command=args.stop_gate_command,
        governance_context_ref=args.governance_context_ref,
        allow_side_effects=False,
        base_commit=base_commit,
        remote=remote,
    )
    artifact = plan_guarded_workcell.build_artifact(plan)
    artifact["capturedAt"] = utc_now()
    artifact["result"] = result
    artifact["worktree"]["status"] = worktree_status
    artifact["sideEffects"] = side_effects
    artifact["governanceContext"]["planOnly"] = False
    artifact["governanceContext"]["sideEffectsAllowed"] = bool(args.allow_side_effects)
    artifact["governanceContext"]["executor"] = "create_guarded_workcell.py"
    artifact["governanceContext"]["reason"] = reason
    artifact["governanceContext"]["remediation"] = remediation
    return artifact


def validate_request(args: argparse.Namespace, workspace: Path) -> tuple[bool, str | None, str | None]:
    if not args.allow_side_effects:
        return False, "Side effects are not allowed.", "Re-run with --allow-side-effects after reviewing the workcell plan."
    protected = set(args.protected_branch or DEFAULT_PROTECTED_BRANCHES)
    if args.branch in protected:
        return False, f"Branch '{args.branch}' is protected.", "Choose a non-protected workcell branch."
    if args.strategy not in {"named", "create-temp", "existing"}:
        return False, f"Strategy '{args.strategy}' does not create or bind a usable workcell.", "Use --strategy named, create-temp, or existing."
    if workspace_exists(workspace) and args.strategy != "existing":
        return False, f"Workspace path already exists: {workspace}", "Use --strategy existing or choose a new workspace path."
    if branch_exists(Path(args.cwd).resolve(), args.branch) and args.strategy != "existing":
        return False, f"Branch already exists: {args.branch}", "Use --strategy existing or choose a new branch."
    return True, None, None


def execute(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    cwd = Path(args.cwd).resolve()
    workspace = Path(args.workspace_path).resolve() if args.workspace_path else default_workspace_path(cwd, args.branch).resolve()
    ok, reason, remediation = validate_request(args, workspace)
    if not ok:
        artifact = build_plan_artifact(
            args=args,
            workspace=workspace,
            result="blocked",
            worktree_status="existing" if workspace.exists() else "not_created",
            side_effects={
                "gitWorktreeCreated": False,
                "branchCreated": False,
                "externalMutationPerformed": False,
                "agentInvoked": False,
            },
            reason=reason,
            remediation=remediation,
        )
        return 2, artifact

    if args.strategy == "existing":
        if not workspace.exists():
            artifact = build_plan_artifact(
                args=args,
                workspace=workspace,
                result="needs_human",
                worktree_status="not_created",
                side_effects={
                    "gitWorktreeCreated": False,
                    "branchCreated": False,
                    "externalMutationPerformed": False,
                    "agentInvoked": False,
                },
                reason=f"Existing workspace does not exist: {workspace}",
                remediation="Create or select an existing workspace path before binding it.",
            )
            return 2, artifact
        artifact = build_plan_artifact(
            args=args,
            workspace=workspace,
            result="ready",
            worktree_status="existing",
            side_effects={
                "gitWorktreeCreated": False,
                "branchCreated": False,
                "externalMutationPerformed": False,
                "agentInvoked": False,
            },
            reason="Existing workspace was bound without mutation.",
            remediation=None,
        )
        return 0, artifact

    workspace.parent.mkdir(parents=True, exist_ok=True)
    result = git_worktree_add(cwd, workspace, args.branch, args.base_ref)
    if result.returncode != 0:
        artifact = build_plan_artifact(
            args=args,
            workspace=workspace,
            result="blocked",
            worktree_status="not_created",
            side_effects={
                "gitWorktreeCreated": False,
                "branchCreated": False,
                "externalMutationPerformed": False,
                "agentInvoked": False,
            },
            reason=f"git worktree add failed: {result.stderr or result.stdout}",
            remediation="Inspect Git state, base ref, branch name, and workspace path, then retry with explicit side-effect authority.",
        )
        return 2, artifact

    artifact = build_plan_artifact(
        args=args,
        workspace=workspace,
        result="ready",
        worktree_status="created",
        side_effects={
            "gitWorktreeCreated": True,
            "branchCreated": True,
            "externalMutationPerformed": False,
            "agentInvoked": False,
        },
        reason="Git worktree and branch were created under explicit side-effect authority.",
        remediation="Run the guarded agent in the workcell and require the stop gate before claiming completion.",
    )
    return 0, artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or bind a guarded AgentPlane workcell under explicit side-effect authority.")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--task-ref", required=True)
    parser.add_argument("--session-ref", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--workspace-path")
    parser.add_argument("--strategy", choices=["named", "create-temp", "existing"], default="named")
    parser.add_argument("--protected-branch", action="append")
    parser.add_argument("--runtime-executor", default="agentplane-local")
    parser.add_argument("--runtime-profile-ref")
    parser.add_argument("--environment-ref")
    parser.add_argument("--agent-command")
    parser.add_argument("--guardrail-adapter", default="claude-code")
    parser.add_argument("--guardrail-hook-command", default=DEFAULT_GUARDRAIL_HOOK_COMMAND)
    parser.add_argument("--decision-log-ref")
    parser.add_argument("--policy-pack-ref")
    parser.add_argument("--no-guardrail", action="store_true")
    parser.add_argument("--stop-gate-command", default=DEFAULT_STOP_GATE_COMMAND)
    parser.add_argument("--stop-gate-artifact-ref")
    parser.add_argument("--no-stop-gate", action="store_true")
    parser.add_argument("--governance-context-ref")
    parser.add_argument("--base-commit")
    parser.add_argument("--remote")
    parser.add_argument("--allow-side-effects", action="store_true")
    parser.add_argument("--out")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, artifact = execute(args)
    encoded = json.dumps(artifact, indent=2, sort_keys=True)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
