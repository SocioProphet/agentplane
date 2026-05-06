#!/usr/bin/env python3
"""Invoke a local command inside a guarded AgentPlane workcell.

This wrapper is intentionally narrow and evidence-first:

- it refuses to execute without --allow-command-execution;
- it reads a GuardedWorkcellArtifact and runs inside its workspace path;
- it sets guardrail and stop-gate environment variables for the command;
- it captures stdout/stderr to files;
- it runs the stop-gate evaluator after the command;
- it only returns success when the command exits 0 and the stop gate passes or is waived.

It does not contact model providers, push branches, open PRs, mutate GitHub, or
mutate CI. Any external effects are the responsibility of the command itself and
must be controlled by guardrail policy and runtime profile.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STOP_GATE_PASS_RESULTS = {"pass", "waived"}
DEFAULT_INVOCATION_DIR = ".sourceos/logs/invocations"
DEFAULT_STOP_GATE_EVALUATOR = "python3 tools/evaluate_stop_gate.py"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return data


def safe_ref_fragment(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)
    cleaned = cleaned.strip("-._")
    return cleaned or "invocation"


def artifact_root(workspace: Path, session_ref: str) -> Path:
    return workspace / DEFAULT_INVOCATION_DIR / safe_ref_fragment(session_ref)


def command_env(workcell: dict[str, Any], invocation_dir: Path, stop_gate_ref: str) -> dict[str, str]:
    guardrail = workcell.get("guardrail") or {}
    stop_gate = workcell.get("stopGate") or {}
    env = os.environ.copy()
    additions = {
        "AGENTPLANE_SESSION_REF": str(workcell.get("sessionRef") or ""),
        "AGENTPLANE_TASK_REF": str(workcell.get("taskRef") or ""),
        "AGENTPLANE_WORKCELL_REPO": str(workcell.get("repo") or ""),
        "AGENTPLANE_WORKCELL_BRANCH": str((workcell.get("worktree") or {}).get("branch") or ""),
        "AGENTPLANE_INVOCATION_DIR": str(invocation_dir),
        "SOURCEOS_GUARDRAIL_DECISION_LOG": str(guardrail.get("decisionLogRef") or ""),
        "SOURCEOS_GUARDRAIL_HOOK_COMMAND": str(guardrail.get("hookCommand") or ""),
        "SOURCEOS_STOP_GATE_ARTIFACT": stop_gate_ref,
        "SOURCEOS_STOP_GATE_EVALUATOR": str(stop_gate.get("evaluatorCommand") or DEFAULT_STOP_GATE_EVALUATOR),
    }
    env.update(additions)
    return env


def run_command(argv: list[str], cwd: Path, env: dict[str, str]) -> CommandResult:
    try:
        completed = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        return CommandResult(returncode=127, stderr=str(exc))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def run_stop_gate(args: argparse.Namespace, workcell: dict[str, Any], workspace: Path, stop_gate_ref: Path) -> tuple[bool, str | None, dict[str, Any] | None]:
    if args.no_stop_gate:
        return False, None, None

    worktree = workcell.get("worktree") or {}
    command = [
        sys.executable,
        str(Path(args.stop_gate_evaluator or "tools/evaluate_stop_gate.py")),
        "--bundle",
        str(workcell.get("bundle") or args.bundle or "guarded-command@0.1.0"),
        "--session-ref",
        str(workcell.get("sessionRef") or args.session_ref),
        "--task-ref",
        str(workcell.get("taskRef") or args.task_ref),
        "--cwd",
        str(workspace),
        "--branch",
        str(args.branch or worktree.get("branch") or "work/guarded-command"),
        "--commit",
        str(args.commit or worktree.get("baseCommit") or "unknown"),
        "--ci-status",
        args.ci_status,
        "--summary-inline",
        args.summary_inline,
        "--out",
        str(stop_gate_ref),
    ]
    if args.clean:
        command.append("--clean")
    else:
        command.append("--no-clean")
    if args.upstream:
        command.extend(["--upstream", args.upstream])
    if args.ahead is not None:
        command.extend(["--ahead", str(args.ahead)])
    if args.behind is not None:
        command.extend(["--behind", str(args.behind)])
    if args.pr_ref:
        command.extend(["--pr-ref", args.pr_ref])
    else:
        command.append("--no-require-pr")
    if args.no_require_ci:
        command.append("--no-require-ci")
    if args.no_require_summary:
        command.append("--no-require-summary")
    decision_log = ((workcell.get("guardrail") or {}).get("decisionLogRef"))
    if decision_log:
        command.extend(["--decision-log", str(workspace / decision_log if not Path(decision_log).is_absolute() else decision_log)])
    if args.human_override_ref:
        command.extend(["--human-override-ref", args.human_override_ref])

    completed = run_command(command, Path.cwd(), os.environ.copy())
    if stop_gate_ref.exists():
        try:
            artifact = load_json(stop_gate_ref)
        except SystemExit:
            artifact = None
    else:
        artifact = None
    if completed.returncode != 0 and artifact is None:
        return True, f"stop gate evaluator failed without artifact: {completed.stderr or completed.stdout}", None
    return True, None if completed.returncode == 0 else (completed.stderr or completed.stdout), artifact


def build_artifact(
    *,
    args: argparse.Namespace,
    workcell: dict[str, Any],
    workspace: Path,
    invocation_dir: Path,
    stdout_ref: Path | None,
    stderr_ref: Path | None,
    started_at: str | None,
    completed_at: str | None,
    exit_code: int | None,
    invocation_status: str,
    result: str,
    reason: str | None,
    remediation: str | None,
    stop_gate_evaluated: bool,
    stop_gate_ref: Path | None,
    stop_gate_result: str | None,
) -> dict[str, Any]:
    return {
        "kind": "GuardedInvocationArtifact",
        "bundle": str(workcell.get("bundle") or args.bundle or "guarded-command@0.1.0"),
        "capturedAt": utc_now(),
        "sessionRef": str(workcell.get("sessionRef") or args.session_ref),
        "taskRef": str(workcell.get("taskRef") or args.task_ref),
        "workcellArtifactRef": str(args.workcell_artifact),
        "workspacePath": str(workspace),
        "command": {
            "argv": args.command,
            "commandClass": args.command_class,
            "shell": False,
            "cwd": str(workspace),
        },
        "invocation": {
            "allowed": bool(args.allow_command_execution),
            "startedAt": started_at,
            "completedAt": completed_at,
            "exitCode": exit_code,
            "status": invocation_status,
            "reason": reason,
            "remediation": remediation,
        },
        "guardrail": {
            "decisionLogRef": (workcell.get("guardrail") or {}).get("decisionLogRef"),
            "hookCommand": (workcell.get("guardrail") or {}).get("hookCommand"),
            "environment": {
                "AGENTPLANE_SESSION_REF": str(workcell.get("sessionRef") or args.session_ref),
                "AGENTPLANE_TASK_REF": str(workcell.get("taskRef") or args.task_ref),
                "SOURCEOS_GUARDRAIL_DECISION_LOG": str((workcell.get("guardrail") or {}).get("decisionLogRef") or ""),
                "SOURCEOS_STOP_GATE_ARTIFACT": str(stop_gate_ref) if stop_gate_ref else "",
            },
        },
        "stopGate": {
            "required": not args.no_stop_gate,
            "evaluated": stop_gate_evaluated,
            "artifactRef": str(stop_gate_ref) if stop_gate_ref else None,
            "result": stop_gate_result,
        },
        "result": result,
        "sideEffects": {
            "localCommandExecuted": started_at is not None,
            "agentProcessInvoked": args.command_class == "agent" and started_at is not None,
            "externalMutationPerformed": False,
            "remoteMutationPerformed": False,
            "providerContacted": False,
        },
        "artifactRefs": {
            "stdoutRef": str(stdout_ref) if stdout_ref else None,
            "stderrRef": str(stderr_ref) if stderr_ref else None,
            "stopGateArtifactRef": str(stop_gate_ref) if stop_gate_ref else None,
            "runArtifactRef": None,
            "replayArtifactRef": None,
        },
        "governanceContext": {
            "invocationDir": str(invocation_dir),
            "sideEffectsAllowed": bool(args.allow_command_execution),
            "requiresStopGateForSuccess": not args.no_stop_gate,
        },
    }


def execute(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    workcell = load_json(Path(args.workcell_artifact).resolve())
    workspace = Path(args.workspace or workcell.get("workspacePath") or (workcell.get("worktree") or {}).get("workspacePath") or "").resolve()
    session_ref = str(workcell.get("sessionRef") or args.session_ref)
    invocation_dir = Path(args.invocation_dir).resolve() if args.invocation_dir else artifact_root(workspace, session_ref).resolve()
    stop_gate_ref = Path(args.stop_gate_artifact or invocation_dir / "stop-gate-artifact.json").resolve()
    invocation_artifact_ref = Path(args.out).resolve() if args.out else invocation_dir / "guarded-invocation-artifact.json"

    if not args.allow_command_execution:
        artifact = build_artifact(
            args=args,
            workcell=workcell,
            workspace=workspace,
            invocation_dir=invocation_dir,
            stdout_ref=None,
            stderr_ref=None,
            started_at=None,
            completed_at=None,
            exit_code=None,
            invocation_status="blocked",
            result="blocked",
            reason="Command execution is not allowed.",
            remediation="Re-run with --allow-command-execution after reviewing the workcell artifact and command.",
            stop_gate_evaluated=False,
            stop_gate_ref=stop_gate_ref,
            stop_gate_result=None,
        )
        return 2, artifact

    if not workspace.exists() or not workspace.is_dir():
        artifact = build_artifact(
            args=args,
            workcell=workcell,
            workspace=workspace,
            invocation_dir=invocation_dir,
            stdout_ref=None,
            stderr_ref=None,
            started_at=None,
            completed_at=None,
            exit_code=None,
            invocation_status="blocked",
            result="blocked",
            reason=f"Workspace path does not exist: {workspace}",
            remediation="Create or bind the guarded workcell before invoking a command.",
            stop_gate_evaluated=False,
            stop_gate_ref=stop_gate_ref,
            stop_gate_result=None,
        )
        return 2, artifact

    invocation_dir.mkdir(parents=True, exist_ok=True)
    stdout_ref = invocation_dir / "stdout.txt"
    stderr_ref = invocation_dir / "stderr.txt"
    env = command_env(workcell, invocation_dir, str(stop_gate_ref))
    started_at = utc_now()
    completed = run_command(args.command, workspace, env)
    completed_at = utc_now()
    stdout_ref.write_text(completed.stdout, encoding="utf-8")
    stderr_ref.write_text(completed.stderr, encoding="utf-8")

    stop_gate_evaluated, stop_gate_error, stop_gate_artifact = run_stop_gate(args, workcell, workspace, stop_gate_ref)
    stop_gate_result = stop_gate_artifact.get("result") if isinstance(stop_gate_artifact, dict) else None

    if completed.returncode != 0:
        result = "failure"
        invocation_status = "failure"
        reason = f"Command exited with code {completed.returncode}."
        remediation = "Inspect stdout/stderr refs, repair the workcell, and re-run the command under guardrail policy."
        exit_code = 2
    elif not args.no_stop_gate and stop_gate_result not in STOP_GATE_PASS_RESULTS:
        result = "needs_human" if stop_gate_result == "needs_human" else "failure"
        invocation_status = result
        reason = stop_gate_error or f"Stop gate result is {stop_gate_result!r}; success requires pass or waived."
        remediation = "Resolve stop-gate failures before claiming completion."
        exit_code = 2
    else:
        result = "success"
        invocation_status = "success"
        reason = "Command completed and stop gate passed or was waived."
        remediation = None
        exit_code = 0

    artifact = build_artifact(
        args=args,
        workcell=workcell,
        workspace=workspace,
        invocation_dir=invocation_dir,
        stdout_ref=stdout_ref,
        stderr_ref=stderr_ref,
        started_at=started_at,
        completed_at=completed_at,
        exit_code=completed.returncode,
        invocation_status=invocation_status,
        result=result,
        reason=reason,
        remediation=remediation,
        stop_gate_evaluated=stop_gate_evaluated,
        stop_gate_ref=stop_gate_ref,
        stop_gate_result=stop_gate_result,
    )
    invocation_artifact_ref.parent.mkdir(parents=True, exist_ok=True)
    invocation_artifact_ref.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return exit_code, artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Invoke a guarded command inside an AgentPlane workcell.")
    parser.add_argument("--workcell-artifact", required=True)
    parser.add_argument("--bundle")
    parser.add_argument("--session-ref", default="urn:srcos:session:guarded-invocation")
    parser.add_argument("--task-ref", default="urn:srcos:task:guarded-invocation")
    parser.add_argument("--workspace")
    parser.add_argument("--invocation-dir")
    parser.add_argument("--out")
    parser.add_argument("--allow-command-execution", action="store_true")
    parser.add_argument("--command-class", choices=["agent", "test", "tool", "shell", "other"], default="tool")
    parser.add_argument("--stop-gate-evaluator", default="tools/evaluate_stop_gate.py")
    parser.add_argument("--stop-gate-artifact")
    parser.add_argument("--no-stop-gate", action="store_true")
    parser.add_argument("--branch")
    parser.add_argument("--commit")
    parser.add_argument("--clean", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--upstream")
    parser.add_argument("--ahead", type=int)
    parser.add_argument("--behind", type=int)
    parser.add_argument("--pr-ref")
    parser.add_argument("--ci-status", default="success")
    parser.add_argument("--summary-inline", default="guarded command invocation completed")
    parser.add_argument("--no-require-ci", action="store_true")
    parser.add_argument("--no-require-summary", action="store_true")
    parser.add_argument("--human-override-ref")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        raise SystemExit("command is required after --")
    exit_code, artifact = execute(args)
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
