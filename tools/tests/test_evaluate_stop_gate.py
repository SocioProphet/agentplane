from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "evaluate_stop_gate.py"
spec = importlib.util.spec_from_file_location("evaluate_stop_gate", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["evaluate_stop_gate"] = module
spec.loader.exec_module(module)

BreakGlassValidation = module.BreakGlassValidation
RepoState = module.RepoState
StopGateConfig = module.StopGateConfig
evaluate_stop_gate = module.evaluate_stop_gate
inspect_decision_log = module.inspect_decision_log
validate_break_glass_override = module.validate_break_glass_override


def base_config(**overrides):
    data = {
        "bundle": "example-agent@0.1.0",
        "session_ref": "urn:srcos:session:test",
        "task_ref": "urn:srcos:task:test",
    }
    data.update(overrides)
    return StopGateConfig(**data)


def good_state(**overrides):
    data = {
        "branch": "work/test",
        "commit": "abc123",
        "clean": True,
        "upstream": "origin/work/test",
        "ahead": 0,
        "behind": 0,
        "pr_ref": "https://github.com/SocioProphet/agentplane/pull/999",
        "ci_status": "success",
        "summary_ref": "summary.md",
        "summary_present": True,
        "unresolved_policy_decision_refs": [],
        "decision_log_ref": ".sourceos/logs/guardrail-decisions.jsonl",
    }
    data.update(overrides)
    return RepoState(**data)


def write_break_glass(path: Path, *, expired: bool = False, state: str = "active", used_count: int = 0) -> Path:
    created = datetime(2026, 5, 5, 0, 0, 0, tzinfo=timezone.utc)
    expires = created - timedelta(minutes=1) if expired else created + timedelta(hours=1)
    artifact = {
        "apiVersion": "policy.fabric.break-glass/v1",
        "kind": "BreakGlassOverride",
        "metadata": {
            "overrideId": "urn:srcos:override:test",
            "createdAt": created.isoformat().replace("+00:00", "Z"),
            "expiresAt": expires.isoformat().replace("+00:00", "Z"),
            "relatedPolicyDecisionId": "decision-1",
            "relatedStopGateId": "sourceos.default.agent-completion",
        },
        "spec": {
            "approver": {"id": "human:tester", "type": "human", "displayName": "tester"},
            "scope": "repository",
            "actionClass": "git",
            "resource": "SocioProphet/agentplane:work/test",
            "reason": "Human reviewed the failure evidence and approved a bounded waiver.",
            "auditRef": "urn:srcos:audit:test",
            "constraints": {
                "singleUse": True,
                "maxUses": 1,
                "allowedCommands": ["git push origin work/test"],
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
            "state": state,
            "usedCount": used_count,
            "lastUsedAt": None,
            "revokedAt": None,
            "revocationReason": None,
        },
    }
    path.write_text(json.dumps(artifact), encoding="utf-8")
    return path


def check_by_id(artifact: dict, check_id: str) -> dict:
    for check in artifact["checks"]:
        if check["checkId"] == check_id:
            return check
    raise AssertionError(f"missing check {check_id}")


def test_stop_gate_passes_for_complete_repo_state() -> None:
    artifact = evaluate_stop_gate(base_config(), good_state())

    assert artifact["kind"] == "StopGateArtifact"
    assert artifact["result"] == "pass"
    assert check_by_id(artifact, "branch-not-protected")["result"] == "pass"
    assert check_by_id(artifact, "worktree-clean")["result"] == "pass"
    assert check_by_id(artifact, "branch-pushed")["result"] == "pass"
    assert check_by_id(artifact, "pull-request-present")["result"] == "pass"
    assert check_by_id(artifact, "ci-green")["result"] == "pass"
    assert check_by_id(artifact, "summary-present")["result"] == "pass"
    assert check_by_id(artifact, "guardrail-clear")["result"] == "pass"


def test_stop_gate_fails_on_protected_branch() -> None:
    artifact = evaluate_stop_gate(base_config(), good_state(branch="main"))

    assert artifact["result"] == "fail"
    check = check_by_id(artifact, "branch-not-protected")
    assert check["result"] == "fail"
    assert "protected" in (check["reason"] or "")
    assert check["remediation"]


def test_stop_gate_fails_on_unpushed_commits() -> None:
    artifact = evaluate_stop_gate(base_config(), good_state(ahead=2))

    assert artifact["result"] == "fail"
    check = check_by_id(artifact, "branch-pushed")
    assert check["result"] == "fail"
    assert "unpushed" in (check["reason"] or "")


def test_stop_gate_needs_human_for_pending_ci() -> None:
    artifact = evaluate_stop_gate(base_config(), good_state(ci_status="pending"))

    assert artifact["result"] == "needs_human"
    assert check_by_id(artifact, "ci-green")["result"] == "needs_human"


def test_stop_gate_fails_on_unresolved_guardrail_decisions() -> None:
    artifact = evaluate_stop_gate(
        base_config(),
        good_state(unresolved_policy_decision_refs=["decision-1", "decision-2"]),
    )

    assert artifact["result"] == "fail"
    check = check_by_id(artifact, "guardrail-clear")
    assert check["result"] == "fail"
    assert check["relatedPolicyDecisionRefs"] == ["decision-1", "decision-2"]


def test_stop_gate_waives_failures_with_human_override() -> None:
    artifact = evaluate_stop_gate(
        base_config(human_override_ref="urn:srcos:override:test"),
        good_state(branch="main", ci_status="failure"),
    )

    assert artifact["result"] == "waived"
    assert artifact["humanOverrideRef"] == "urn:srcos:override:test"


def test_valid_break_glass_override_waives_failures(tmp_path) -> None:  # type: ignore[no-untyped-def]
    override = write_break_glass(tmp_path / "break-glass.json")
    validation = validate_break_glass_override(override, now=datetime(2026, 5, 5, 0, 30, 0, tzinfo=timezone.utc))
    artifact = evaluate_stop_gate(
        base_config(break_glass=validation),
        good_state(branch="main", ci_status="failure"),
    )

    assert validation.valid is True
    assert artifact["result"] == "waived"
    assert artifact["breakGlassOverrideRef"] == str(override)
    assert artifact["artifactRefs"]["breakGlassOverrideRef"] == str(override)
    assert artifact["governanceContext"]["breakGlass"]["overrideId"] == "urn:srcos:override:test"
    assert check_by_id(artifact, "break-glass-valid")["result"] == "pass"


def test_invalid_break_glass_override_fails_gate(tmp_path) -> None:  # type: ignore[no-untyped-def]
    override = write_break_glass(tmp_path / "expired-break-glass.json", expired=True)
    validation = validate_break_glass_override(override, now=datetime(2026, 5, 5, 0, 30, 0, tzinfo=timezone.utc))
    artifact = evaluate_stop_gate(
        base_config(break_glass=validation),
        good_state(branch="main"),
    )

    assert validation.valid is False
    assert artifact["result"] == "fail"
    assert check_by_id(artifact, "break-glass-valid")["result"] == "fail"


def test_consumed_break_glass_override_is_invalid(tmp_path) -> None:  # type: ignore[no-untyped-def]
    override = write_break_glass(tmp_path / "consumed-break-glass.json", used_count=1)
    validation = validate_break_glass_override(override, now=datetime(2026, 5, 5, 0, 30, 0, tzinfo=timezone.utc))

    assert validation.valid is False
    assert "remaining uses" in (validation.reason or "")


def test_inspect_decision_log_extracts_blocking_decisions(tmp_path) -> None:
    log = tmp_path / "guardrail-decisions.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps({"decisionId": "allow-1", "decision": "allow", "severity": "info"}),
                json.dumps({"decisionId": "deny-1", "decision": "deny", "severity": "critical"}),
                json.dumps({"decisionId": "redact-1", "decision": "redact", "severity": "critical"}),
                "not-json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert inspect_decision_log(log) == ["deny-1", "redact-1", f"{log}:line-4:invalid-json"]
