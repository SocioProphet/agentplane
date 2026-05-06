#!/usr/bin/env python3
"""Deterministic smoke validation for the guarded workcell executor."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "tools" / "create_guarded_workcell.py"


def die(message: str) -> None:
    print(f"[guarded-workcell-executor] ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def checked(args: list[str], cwd: Path) -> str:
    completed = run(args, cwd)
    if completed.returncode != 0:
        die(f"command failed: {' '.join(args)}\nstdout={completed.stdout}\nstderr={completed.stderr}")
    return completed.stdout.strip()


def init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    checked(["git", "init", "-b", "main"], repo)
    checked(["git", "config", "user.email", "agentplane@example.invalid"], repo)
    checked(["git", "config", "user.name", "AgentPlane Test"], repo)
    (repo / "README.md").write_text("# guarded workcell validation\n", encoding="utf-8")
    checked(["git", "add", "README.md"], repo)
    checked(["git", "commit", "-m", "initial"], repo)
    return repo


def run_executor(args: list[str]) -> tuple[int, dict]:
    completed = run([sys.executable, str(EXECUTOR), *args], ROOT)
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        die(f"executor did not emit JSON: {exc}; stdout={completed.stdout!r}; stderr={completed.stderr!r}")
    return completed.returncode, data


def base_args(repo: Path, workspace: Path) -> list[str]:
    return [
        "--bundle",
        "example-agent@0.1.0",
        "--repo",
        "SocioProphet/agentplane",
        "--base-ref",
        "main",
        "--task-ref",
        "urn:srcos:task:validate-workcell-executor",
        "--session-ref",
        "urn:srcos:session:validate-workcell-executor",
        "--branch",
        "work/validate-workcell-executor",
        "--cwd",
        str(repo),
        "--workspace-path",
        str(workspace),
        "--base-commit",
        "abc123",
        "--remote",
        "https://github.com/SocioProphet/agentplane.git",
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = init_repo(root)
        blocked_workspace = root / "blocked-workcell"
        code, blocked = run_executor(base_args(repo, blocked_workspace))
        if code == 0:
            die(f"executor without --allow-side-effects unexpectedly passed: {blocked}")
        if blocked.get("result") != "blocked":
            die(f"expected blocked artifact without side-effect authority: {blocked}")
        if blocked_workspace.exists():
            die("blocked run unexpectedly created a workspace")

        workspace = root / "created-workcell"
        out = root / "guarded-workcell-artifact.json"
        code, created = run_executor([*base_args(repo, workspace), "--allow-side-effects", "--out", str(out)])
        if code != 0:
            die(f"executor with --allow-side-effects failed: {created}")
        if created.get("result") != "ready":
            die(f"expected ready artifact after worktree creation: {created}")
        if created["sideEffects"]["gitWorktreeCreated"] is not True or created["sideEffects"]["branchCreated"] is not True:
            die(f"expected worktree/branch side-effect evidence: {created['sideEffects']}")
        if created["sideEffects"]["agentInvoked"] is not False or created["sideEffects"]["externalMutationPerformed"] is not False:
            die(f"unexpected external side effects recorded: {created['sideEffects']}")
        if not workspace.exists() or not (workspace / "README.md").exists():
            die("expected git worktree to exist with README.md")
        if not out.exists():
            die("expected artifact output file to exist")

        branch_check = checked(["git", "rev-parse", "--verify", "work/validate-workcell-executor"], repo)
        if not branch_check:
            die("expected workcell branch to exist")

    print("[guarded-workcell-executor] OK: executor smoke validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
