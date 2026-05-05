from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "plan_guarded_workcell.py"
spec = importlib.util.spec_from_file_location("plan_guarded_workcell", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["plan_guarded_workcell"] = module
spec.loader.exec_module(module)

WorkcellPlan = module.WorkcellPlan
build_artifact = module.build_artifact
main = module.main


def base_plan(**overrides):
    data = {
        "bundle": "example-agent@0.1.0",
        "repo": "SocioProphet/agentplane",
        "base_ref": "main",
        "task_ref": "urn:srcos:task:test",
        "session_ref": "urn:srcos:session:test",
        "branch": "work/test",
        "workspace_path": None,
        "strategy": "plan-only",
        "runtime_executor": "agentplane-local",
        "runtime_profile_ref": None,
        "environment_ref": None,
        "agent_command": None,
        "guardrail_enabled": True,
        "guardrail_adapter": "claude-code",
        "guardrail_hook_command": "guardrail-fabric-hook --write-log",
        "decision_log_ref": None,
        "policy_pack_ref": None,
        "stop_gate_enabled": True,
        "stop_gate_artifact_ref": None,
        "stop_gate_command": "python3 tools/evaluate_stop_gate.py",
        "governance_context_ref": None,
        "allow_side_effects": False,
        "base_commit": "abc123",
        "remote": "https://github.com/SocioProphet/agentplane.git",
    }
    data.update(overrides)
    return WorkcellPlan(**data)


def test_plan_only_workcell_artifact_is_planned_and_side_effect_free() -> None:
    artifact = build_artifact(base_plan())

    assert artifact["kind"] == "GuardedWorkcellArtifact"
    assert artifact["result"] == "planned"
    assert artifact["repo"] == "SocioProphet/agentplane"
    assert artifact["baseRef"] == "main"
    assert artifact["worktree"]["strategy"] == "plan-only"
    assert artifact["worktree"]["status"] == "planned"
    assert artifact["guardrail"]["enabled"] is True
    assert artifact["guardrail"]["adapter"] == "claude-code"
    assert artifact["guardrail"]["decisionLogRef"] == ".sourceos/logs/guardrail-decisions.jsonl"
    assert artifact["stopGate"]["enabled"] is True
    assert artifact["stopGate"]["artifactRef"] == ".sourceos/logs/stop-gate-artifact.json"
    assert artifact["sideEffects"] == {
        "gitWorktreeCreated": False,
        "branchCreated": False,
        "externalMutationPerformed": False,
        "agentInvoked": False,
    }


def test_existing_strategy_without_workspace_needs_human() -> None:
    artifact = build_artifact(base_plan(strategy="existing", workspace_path=None))

    assert artifact["result"] == "needs_human"
    assert artifact["worktree"]["status"] == "not_created"


def test_disabled_guardrail_needs_human() -> None:
    artifact = build_artifact(base_plan(guardrail_enabled=False))

    assert artifact["result"] == "needs_human"
    assert artifact["guardrail"]["hookCommand"] is None
    assert artifact["guardrail"]["decisionLogRef"] is None


def test_side_effect_permission_posture_is_blocked_but_non_mutating() -> None:
    artifact = build_artifact(base_plan(allow_side_effects=True, strategy="named"))

    assert artifact["result"] == "blocked"
    assert artifact["governanceContext"]["sideEffectsAllowed"] is True
    assert artifact["sideEffects"]["gitWorktreeCreated"] is False
    assert artifact["sideEffects"]["branchCreated"] is False
    assert artifact["sideEffects"]["agentInvoked"] is False


def test_cli_writes_artifact(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "guarded-workcell-artifact.json"
    exit_code = main([
        "--bundle",
        "example-agent@0.1.0",
        "--repo",
        "SocioProphet/agentplane",
        "--base-ref",
        "main",
        "--task-ref",
        "urn:srcos:task:test",
        "--session-ref",
        "urn:srcos:session:test",
        "--branch",
        "work/test",
        "--base-commit",
        "abc123",
        "--remote",
        "https://github.com/SocioProphet/agentplane.git",
        "--out",
        str(out),
    ])
    captured = capsys.readouterr()
    stdout_artifact = json.loads(captured.out)
    file_artifact = json.loads(out.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout_artifact["kind"] == "GuardedWorkcellArtifact"
    assert stdout_artifact["sessionRef"] == file_artifact["sessionRef"]
    assert file_artifact["result"] == "planned"
