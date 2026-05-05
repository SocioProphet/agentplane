#!/usr/bin/env python3
"""Plan a guarded AgentPlane workcell.

This tool emits a GuardedWorkcellArtifact that binds a repo/task/session to
SourceOS guardrail and stop-gate contracts. It is plan-only by default: it does
not create branches, create worktrees, invoke agents, contact providers, or
mutate external systems.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_GUARDRAIL_HOOK_COMMAND = "guardrail-fabric-hook --write-log"
DEFAULT_STOP_GATE_COMMAND = "python3 tools/evaluate_stop_gate.py"
DEFAULT_POLICY_DECISION_SCHEMA_REF = "schemas/policy-decision-artifact.schema.v0.1.json"
DEFAULT_STOP_GATE_SCHEMA_REF = "schemas/stop-gate-artifact.schema.v0.1.json"
DEFAULT_WORKCELL_SCHEMA_REF = "schemas/guarded-workcell-artifact.schema.v0.1.json"


@dataclass(frozen=True)
class WorkcellPlan:
    bundle: str
    repo: str
    base_ref: str
    task_ref: str
    session_ref: str
    branch: str
    workspace_path: str | None
    strategy: str
    runtime_executor: str
    runtime_profile_ref: str | None
    environment_ref: str | None
    agent_command: str | None
    guardrail_enabled: bool
    guardrail_adapter: str
    guardrail_hook_command: str | None
    decision_log_ref: str | None
    policy_pack_ref: str | None
    stop_gate_enabled: bool
    stop_gate_artifact_ref: str | None
    stop_gate_command: str | None
    governance_context_ref: str | None
    allow_side_effects: bool = False
    base_commit: str | None = None
    remote: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_git(cwd: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def infer_git_defaults(cwd: Path) -> dict[str, str | None]:
    return {
        "baseCommit": run_git(cwd, ["rev-parse", "HEAD"]),
        "remote": run_git(cwd, ["remote", "get-url", "origin"]),
    }


def artifact_result(plan: WorkcellPlan) -> str:
    if plan.allow_side_effects:
        return "blocked"
    if not plan.repo or not plan.base_ref or not plan.task_ref or not plan.session_ref or not plan.branch:
        return "blocked"
    if not plan.guardrail_enabled or not plan.stop_gate_enabled:
        return "needs_human"
    if plan.strategy == "existing" and not plan.workspace_path:
        return "needs_human"
    return "planned"


def worktree_status(strategy: str, workspace_path: str | None) -> str:
    if strategy == "existing":
        return "existing" if workspace_path else "not_created"
    return "planned"


def build_artifact(plan: WorkcellPlan) -> dict[str, Any]:
    defaults = infer_git_defaults(Path.cwd())
    base_commit = plan.base_commit or defaults["baseCommit"]
    remote = plan.remote or defaults["remote"]
    stop_gate_ref = plan.stop_gate_artifact_ref or ".sourceos/logs/stop-gate-artifact.json"
    decision_log_ref = plan.decision_log_ref or ".sourceos/logs/guardrail-decisions.jsonl"

    return {
        "kind": "GuardedWorkcellArtifact",
        "bundle": plan.bundle,
        "capturedAt": utc_now(),
        "sessionRef": plan.session_ref,
        "taskRef": plan.task_ref,
        "repo": plan.repo,
        "baseRef": plan.base_ref,
        "worktree": {
            "strategy": plan.strategy,
            "branch": plan.branch,
            "workspacePath": plan.workspace_path,
            "status": worktree_status(plan.strategy, plan.workspace_path),
            "baseCommit": base_commit,
            "remote": remote,
        },
        "guardrail": {
            "enabled": plan.guardrail_enabled,
            "adapter": plan.guardrail_adapter,
            "hookCommand": plan.guardrail_hook_command if plan.guardrail_enabled else None,
            "decisionLogRef": decision_log_ref if plan.guardrail_enabled else None,
            "policyPackRef": plan.policy_pack_ref,
            "policyDecisionArtifactSchemaRef": DEFAULT_POLICY_DECISION_SCHEMA_REF,
        },
        "stopGate": {
            "enabled": plan.stop_gate_enabled,
            "evaluatorCommand": plan.stop_gate_command if plan.stop_gate_enabled else None,
            "artifactRef": stop_gate_ref if plan.stop_gate_enabled else None,
            "schemaRef": DEFAULT_STOP_GATE_SCHEMA_REF,
        },
        "runtime": {
            "executor": plan.runtime_executor,
            "profileRef": plan.runtime_profile_ref,
            "environmentRef": plan.environment_ref,
            "agentCommand": plan.agent_command,
        },
        "result": artifact_result(plan),
        "sideEffects": {
            "gitWorktreeCreated": False,
            "branchCreated": False,
            "externalMutationPerformed": False,
            "agentInvoked": False,
        },
        "artifactRefs": {
            "policyDecisionArtifactRef": None,
            "stopGateArtifactRef": stop_gate_ref if plan.stop_gate_enabled else None,
            "sessionArtifactRef": None,
            "replayArtifactRef": None,
        },
        "governanceContext": {
            "governanceContextRef": plan.governance_context_ref,
            "workcellSchemaRef": DEFAULT_WORKCELL_SCHEMA_REF,
            "planOnly": True,
            "sideEffectsAllowed": plan.allow_side_effects,
        },
    }


def build_plan(args: argparse.Namespace) -> WorkcellPlan:
    return WorkcellPlan(
        bundle=args.bundle,
        repo=args.repo,
        base_ref=args.base_ref,
        task_ref=args.task_ref,
        session_ref=args.session_ref,
        branch=args.branch,
        workspace_path=args.workspace_path,
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
        allow_side_effects=args.allow_side_effects,
        base_commit=args.base_commit,
        remote=args.remote,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a guarded AgentPlane workcell and emit GuardedWorkcellArtifact JSON.")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--task-ref", required=True)
    parser.add_argument("--session-ref", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--workspace-path")
    parser.add_argument("--strategy", choices=["plan-only", "existing", "named", "create-temp"], default="plan-only")
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
    parser.add_argument("--allow-side-effects", action="store_true", help="Record side-effect permission posture only; this tool still performs no side effects.")
    parser.add_argument("--out", help="Path to write GuardedWorkcellArtifact JSON. Defaults to stdout only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact = build_artifact(build_plan(args))
    encoded = json.dumps(artifact, indent=2, sort_keys=True)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if artifact["result"] in {"planned", "ready"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
