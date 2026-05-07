from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

MODULE_PATH = TOOLS_DIR / "invoke_guarded_command.py"
spec = importlib.util.spec_from_file_location("invoke_guarded_command", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["invoke_guarded_command"] = module
spec.loader.exec_module(module)

main = module.main


def write_workcell(tmp_path: Path, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    artifact = {
        "kind": "GuardedWorkcellArtifact",
        "bundle": "example-agent@0.1.0",
        "capturedAt": "2026-05-05T00:00:00Z",
        "sessionRef": "urn:srcos:session:test-invocation",
        "taskRef": "urn:srcos:task:test-invocation",
        "repo": "SocioProphet/agentplane",
        "baseRef": "main",
        "worktree": {
            "strategy": "existing",
            "branch": "work/test-invocation",
            "workspacePath": str(workspace),
            "status": "existing",
            "baseCommit": "abc123",
            "remote": "https://github.com/SocioProphet/agentplane.git",
        },
        "guardrail": {
            "enabled": True,
            "adapter": "claude-code",
            "hookCommand": "guardrail-fabric-hook --write-log",
            "decisionLogRef": ".sourceos/logs/guardrail-decisions.jsonl",
            "policyPackRef": None,
            "policyDecisionArtifactSchemaRef": "schemas/policy-decision-artifact.schema.v0.1.json",
        },
        "stopGate": {
            "enabled": True,
            "evaluatorCommand": "python3 tools/evaluate_stop_gate.py",
            "artifactRef": ".sourceos/logs/stop-gate-artifact.json",
            "schemaRef": "schemas/stop-gate-artifact.schema.v0.1.json",
        },
        "runtime": {
            "executor": "agentplane-local",
            "profileRef": None,
            "environmentRef": None,
            "agentCommand": None,
        },
        "result": "ready",
        "sideEffects": {
            "gitWorktreeCreated": False,
            "branchCreated": False,
            "externalMutationPerformed": False,
            "agentInvoked": False,
        },
        "artifactRefs": {
            "policyDecisionArtifactRef": None,
            "stopGateArtifactRef": ".sourceos/logs/stop-gate-artifact.json",
            "sessionArtifactRef": None,
            "replayArtifactRef": None,
        },
        "governanceContext": None,
    }
    path = tmp_path / "guarded-workcell-artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def write_break_glass(path: Path) -> Path:
    artifact = {
        "apiVersion": "policy.fabric.break-glass/v1",
        "kind": "BreakGlassOverride",
        "metadata": {
            "overrideId": "urn:srcos:override:test-invocation",
            "createdAt": "2026-05-05T00:00:00Z",
            "expiresAt": "2099-05-05T00:00:00Z",
            "relatedPolicyDecisionId": "deny-1",
            "relatedStopGateId": "sourceos.default.agent-completion",
        },
        "spec": {
            "approver": {"id": "human:tester", "type": "human", "displayName": "tester"},
            "scope": "repository",
            "actionClass": "git",
            "resource": "SocioProphet/agentplane:work/test-invocation",
            "reason": "Human approved a bounded stop-gate waiver for test evidence.",
            "auditRef": "urn:srcos:audit:test-invocation",
            "constraints": {
                "singleUse": True,
                "maxUses": 1,
                "allowedCommands": [],
                "allowedPaths": [],
                "allowedProviders": [],
            },
            "signature": {
                "scheme": "sourceos-dev-placeholder-v0",
                "keyRef": "did:example:tester#approval",
                "signature": "placeholder",
            },
        },
        "status": {
            "state": "active",
            "usedCount": 0,
            "lastUsedAt": None,
            "revokedAt": None,
            "revocationReason": None,
        },
    }
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def common_args(workcell: Path, invocation_dir: Path) -> list[str]:
    return [
        "--workcell-artifact",
        str(workcell),
        "--invocation-dir",
        str(invocation_dir),
        "--branch",
        "work/test-invocation",
        "--commit",
        "abc123",
        "--upstream",
        "origin/work/test-invocation",
        "--ahead",
        "0",
        "--behind",
        "0",
        "--pr-ref",
        "https://github.com/SocioProphet/agentplane/pull/0",
        "--ci-status",
        "success",
        "--summary-inline",
        "guarded invocation test completed",
    ]


def test_blocks_without_command_execution_authority(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    workspace = tmp_path / "workspace"
    workcell = write_workcell(tmp_path, workspace)
    invocation_dir = tmp_path / "invocation"

    exit_code = main([*common_args(workcell, invocation_dir), "--", sys.executable, "-c", "print('should-not-run')"])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 2
    assert artifact["result"] == "blocked"
    assert artifact["invocation"]["allowed"] is False
    assert artifact["sideEffects"]["localCommandExecuted"] is False
    assert not (invocation_dir / "stdout.txt").exists()


def test_invocation_success_requires_stop_gate_pass(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    workspace = tmp_path / "workspace"
    workcell = write_workcell(tmp_path, workspace)
    invocation_dir = tmp_path / "invocation"
    out = tmp_path / "guarded-invocation-artifact.json"

    exit_code = main([
        *common_args(workcell, invocation_dir),
        "--allow-command-execution",
        "--out",
        str(out),
        "--",
        sys.executable,
        "-c",
        "print('ok')",
    ])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 0
    assert artifact["kind"] == "GuardedInvocationArtifact"
    assert artifact["result"] == "success"
    assert artifact["invocation"]["exitCode"] == 0
    assert artifact["stopGate"]["evaluated"] is True
    assert artifact["stopGate"]["result"] in {"pass", "waived"}
    assert artifact["sideEffects"]["localCommandExecuted"] is True
    assert artifact["sideEffects"]["agentProcessInvoked"] is False
    assert artifact["sideEffects"]["remoteMutationPerformed"] is False
    assert (invocation_dir / "stdout.txt").read_text(encoding="utf-8").strip() == "ok"
    assert json.loads(out.read_text(encoding="utf-8"))["sessionRef"] == artifact["sessionRef"]


def test_command_failure_returns_failure_even_if_stop_gate_passes(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    workspace = tmp_path / "workspace"
    workcell = write_workcell(tmp_path, workspace)
    invocation_dir = tmp_path / "invocation"

    exit_code = main([
        *common_args(workcell, invocation_dir),
        "--allow-command-execution",
        "--",
        sys.executable,
        "-c",
        "import sys; print('bad'); sys.exit(3)",
    ])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 2
    assert artifact["result"] == "failure"
    assert artifact["invocation"]["exitCode"] == 3
    assert artifact["sideEffects"]["localCommandExecuted"] is True
    assert (invocation_dir / "stdout.txt").read_text(encoding="utf-8").strip() == "bad"


def test_stop_gate_failure_blocks_success(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    workspace = tmp_path / "workspace"
    workcell = write_workcell(tmp_path, workspace)
    invocation_dir = tmp_path / "invocation"
    decision_log = workspace / ".sourceos" / "logs" / "guardrail-decisions.jsonl"
    decision_log.parent.mkdir(parents=True, exist_ok=True)
    decision_log.write_text(json.dumps({"decisionId": "deny-1", "decision": "deny", "severity": "critical"}) + "\n", encoding="utf-8")

    exit_code = main([
        *common_args(workcell, invocation_dir),
        "--allow-command-execution",
        "--",
        sys.executable,
        "-c",
        "print('ok')",
    ])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 2
    assert artifact["result"] == "failure"
    assert artifact["invocation"]["exitCode"] == 0
    assert artifact["stopGate"]["evaluated"] is True
    assert artifact["stopGate"]["result"] == "fail"
    assert "Stop gate" in (artifact["invocation"]["reason"] or "")


def test_break_glass_override_waives_stop_gate_failure(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    workspace = tmp_path / "workspace"
    workcell = write_workcell(tmp_path, workspace)
    invocation_dir = tmp_path / "invocation"
    break_glass = write_break_glass(tmp_path / "break-glass.json")
    decision_log = workspace / ".sourceos" / "logs" / "guardrail-decisions.jsonl"
    decision_log.parent.mkdir(parents=True, exist_ok=True)
    decision_log.write_text(json.dumps({"decisionId": "deny-1", "decision": "deny", "severity": "critical"}) + "\n", encoding="utf-8")

    exit_code = main([
        *common_args(workcell, invocation_dir),
        "--allow-command-execution",
        "--break-glass-override",
        str(break_glass),
        "--",
        sys.executable,
        "-c",
        "print('ok')",
    ])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 0
    assert artifact["result"] == "success"
    assert artifact["stopGate"]["result"] == "waived"
    assert artifact["stopGate"]["breakGlassOverrideRef"] == str(break_glass.resolve())
    assert artifact["artifactRefs"]["breakGlassOverrideRef"] == str(break_glass.resolve())
    assert artifact["guardrail"]["environment"]["SOURCEOS_BREAK_GLASS_OVERRIDE"] == str(break_glass.resolve())
