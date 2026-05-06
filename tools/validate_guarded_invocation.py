#!/usr/bin/env python3
"""Deterministic smoke validation for guarded command invocation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVOKER = ROOT / "tools" / "invoke_guarded_command.py"


def die(message: str) -> None:
    print(f"[guarded-invocation] ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def run_invoker(args: list[str]) -> tuple[int, dict]:
    completed = subprocess.run(
        [sys.executable, str(INVOKER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        die(f"invoker did not emit JSON: {exc}; stdout={completed.stdout!r}; stderr={completed.stderr!r}")
    return completed.returncode, data


def write_workcell(root: Path, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    artifact = {
        "kind": "GuardedWorkcellArtifact",
        "bundle": "example-agent@0.1.0",
        "capturedAt": "2026-05-05T00:00:00Z",
        "sessionRef": "urn:srcos:session:validate-guarded-invocation",
        "taskRef": "urn:srcos:task:validate-guarded-invocation",
        "repo": "SocioProphet/agentplane",
        "baseRef": "main",
        "worktree": {
            "strategy": "existing",
            "branch": "work/validate-guarded-invocation",
            "workspacePath": str(workspace),
            "status": "existing",
            "baseCommit": "abc123",
            "remote": "https://github.com/SocioProphet/agentplane.git"
        },
        "guardrail": {
            "enabled": True,
            "adapter": "claude-code",
            "hookCommand": "guardrail-fabric-hook --write-log",
            "decisionLogRef": ".sourceos/logs/guardrail-decisions.jsonl",
            "policyPackRef": None,
            "policyDecisionArtifactSchemaRef": "schemas/policy-decision-artifact.schema.v0.1.json"
        },
        "stopGate": {
            "enabled": True,
            "evaluatorCommand": "python3 tools/evaluate_stop_gate.py",
            "artifactRef": ".sourceos/logs/stop-gate-artifact.json",
            "schemaRef": "schemas/stop-gate-artifact.schema.v0.1.json"
        },
        "runtime": {
            "executor": "agentplane-local",
            "profileRef": None,
            "environmentRef": None,
            "agentCommand": None
        },
        "result": "ready",
        "sideEffects": {
            "gitWorktreeCreated": False,
            "branchCreated": False,
            "externalMutationPerformed": False,
            "agentInvoked": False
        },
        "artifactRefs": {
            "policyDecisionArtifactRef": None,
            "stopGateArtifactRef": ".sourceos/logs/stop-gate-artifact.json",
            "sessionArtifactRef": None,
            "replayArtifactRef": None
        },
        "governanceContext": None
    }
    path = root / "guarded-workcell-artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def base_args(workcell: Path, invocation_dir: Path) -> list[str]:
    return [
        "--workcell-artifact", str(workcell),
        "--invocation-dir", str(invocation_dir),
        "--branch", "work/validate-guarded-invocation",
        "--commit", "abc123",
        "--upstream", "origin/work/validate-guarded-invocation",
        "--ahead", "0",
        "--behind", "0",
        "--pr-ref", "https://github.com/SocioProphet/agentplane/pull/0",
        "--ci-status", "success",
        "--summary-inline", "guarded invocation validation completed"
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "workspace"
        workcell = write_workcell(root, workspace)
        invocation_dir = root / "invocation"

        code, blocked = run_invoker([
            *base_args(workcell, invocation_dir),
            "--",
            sys.executable,
            "-c",
            "print('should-not-run')"
        ])
        if code == 0:
            die(f"invocation without authority unexpectedly passed: {blocked}")
        if blocked.get("result") != "blocked" or blocked["sideEffects"]["localCommandExecuted"] is not False:
            die(f"expected blocked non-executed artifact: {blocked}")

        out = root / "guarded-invocation-artifact.json"
        code, success = run_invoker([
            *base_args(workcell, invocation_dir),
            "--allow-command-execution",
            "--out", str(out),
            "--",
            sys.executable,
            "-c",
            "print('guarded-ok')"
        ])
        if code != 0:
            die(f"authorized invocation failed: {success}")
        if success.get("kind") != "GuardedInvocationArtifact" or success.get("result") != "success":
            die(f"expected successful GuardedInvocationArtifact: {success}")
        if success["stopGate"]["result"] not in {"pass", "waived"}:
            die(f"expected passing stop gate: {success['stopGate']}")
        stdout_ref = Path(success["artifactRefs"]["stdoutRef"])
        if stdout_ref.read_text(encoding="utf-8").strip() != "guarded-ok":
            die("stdout artifact did not capture command output")
        if not out.exists():
            die("expected --out invocation artifact")

    print("[guarded-invocation] OK: guarded invocation smoke validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
