#!/usr/bin/env python3
"""Evaluate SourceOS agent completion stop gates.

The evaluator emits a StopGateArtifact without reimplementing guardrail policy
logic. It consumes repo state, CI/PR/summary evidence, guardrail decision logs,
and optional PolicyFabric BreakGlassOverride artifacts, then produces actionable
pass/fail/needs-human/waived evidence for AgentPlane.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

TERMINAL_BLOCKING_DECISIONS = {"deny", "quarantine", "defer", "escalate"}
DEFAULT_PROTECTED_BRANCHES = ("main", "master", "trunk", "prod", "production")
POLICYFABRIC_BREAK_GLASS_API = "policy.fabric.break-glass/v1"
POLICYFABRIC_BREAK_GLASS_KIND = "BreakGlassOverride"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class RepoState:
    branch: str | None
    commit: str | None
    clean: bool | None
    upstream: str | None
    ahead: int | None
    behind: int | None
    pr_ref: str | None
    ci_status: str | None
    summary_ref: str | None
    summary_present: bool | None
    unresolved_policy_decision_refs: list[str]
    decision_log_ref: str | None = None


@dataclass(frozen=True)
class BreakGlassValidation:
    ref: str | None = None
    override_id: str | None = None
    valid: bool = False
    reason: str | None = None
    audit_ref: str | None = None
    approver_ref: str | None = None
    action_class: str | None = None
    resource: str | None = None


@dataclass(frozen=True)
class StopGateConfig:
    bundle: str
    session_ref: str
    task_ref: str | None = None
    gate_id: str = "sourceos.default.agent-completion"
    gate_name: str = "SourceOS Default Agent Completion Gate"
    gate_policy_ref: str | None = "sourceos/agentplane/default-stop-gates@0.1.0"
    protected_branches: tuple[str, ...] = DEFAULT_PROTECTED_BRANCHES
    require_pr: bool = True
    require_ci: bool = True
    require_summary: bool = True
    require_decision_log: bool = False
    human_override_ref: str | None = None
    break_glass: BreakGlassValidation = BreakGlassValidation()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_datetime(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def run_command(args: list[str], cwd: Path) -> CommandResult:
    try:
        completed = subprocess.run(args, cwd=cwd, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return CommandResult(returncode=127, stderr=str(exc))
    return CommandResult(completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def git_value(cwd: Path, args: list[str], runner: Callable[[list[str], Path], CommandResult] = run_command) -> str | None:
    result = runner(["git", *args], cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def inspect_git_state(cwd: Path, runner: Callable[[list[str], Path], CommandResult] = run_command) -> dict[str, Any]:
    branch = git_value(cwd, ["rev-parse", "--abbrev-ref", "HEAD"], runner)
    commit = git_value(cwd, ["rev-parse", "HEAD"], runner)
    status = git_value(cwd, ["status", "--porcelain"], runner)
    clean = status == "" if status is not None else None
    upstream = git_value(cwd, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], runner)

    ahead = None
    behind = None
    if upstream:
        counts = git_value(cwd, ["rev-list", "--left-right", "--count", "@{u}...HEAD"], runner)
        if counts:
            parts = counts.split()
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                behind = int(parts[0])
                ahead = int(parts[1])

    return {
        "branch": branch,
        "commit": commit,
        "clean": clean,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
    }


def inspect_pr_ref(cwd: Path, runner: Callable[[list[str], Path], CommandResult] = run_command) -> str | None:
    result = runner(["gh", "pr", "view", "--json", "url", "--jq", ".url"], cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def inspect_decision_log(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []

    unresolved: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                unresolved.append(f"{path}:line-{line_no}:invalid-json")
                continue

            decision = str(event.get("decision", "")).lower()
            severity = str(event.get("severity", "")).lower()
            decision_id = str(event.get("decisionId") or f"{path}:line-{line_no}")
            if decision in TERMINAL_BLOCKING_DECISIONS or (decision == "redact" and severity in {"high", "critical"}):
                unresolved.append(decision_id)
    return unresolved


def validate_break_glass_override(path: Path | None, *, now: datetime | None = None) -> BreakGlassValidation:
    if path is None:
        return BreakGlassValidation()
    ref = str(path)
    if not path.exists():
        return BreakGlassValidation(ref=ref, valid=False, reason=f"BreakGlassOverride artifact not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return BreakGlassValidation(ref=ref, valid=False, reason=f"BreakGlassOverride artifact is invalid JSON: {exc}")
    if not isinstance(data, dict):
        return BreakGlassValidation(ref=ref, valid=False, reason="BreakGlassOverride artifact must be a JSON object")

    try:
        if data.get("apiVersion") != POLICYFABRIC_BREAK_GLASS_API:
            raise ValueError("apiVersion must be policy.fabric.break-glass/v1")
        if data.get("kind") != POLICYFABRIC_BREAK_GLASS_KIND:
            raise ValueError("kind must be BreakGlassOverride")
        metadata = data["metadata"]
        spec = data["spec"]
        status = data["status"]
        override_id = str(metadata["overrideId"])
        created_at = parse_datetime(str(metadata["createdAt"]), "metadata.createdAt")
        expires_at = parse_datetime(str(metadata["expiresAt"]), "metadata.expiresAt")
        clock = now or datetime.now(timezone.utc)
        if expires_at <= created_at:
            raise ValueError("expiresAt must be after createdAt")
        if expires_at <= clock:
            raise ValueError("override is expired")

        approver = spec["approver"]
        if approver.get("type") != "human":
            raise ValueError("approver.type must be human")
        if not str(approver.get("id") or "").strip():
            raise ValueError("approver.id is required")
        if not str(spec.get("reason") or "").strip():
            raise ValueError("reason is required")
        if not str(spec.get("auditRef") or "").strip():
            raise ValueError("auditRef is required")
        if spec.get("signature") is None:
            raise ValueError("signature object is required")

        constraints = spec["constraints"]
        max_uses = int(constraints["maxUses"])
        used_count = int(status["usedCount"])
        if bool(constraints.get("singleUse")) and max_uses != 1:
            raise ValueError("singleUse overrides must have maxUses=1")
        if used_count >= max_uses:
            raise ValueError("override has no remaining uses")
        if status.get("state") != "active":
            raise ValueError("override status.state must be active")

        return BreakGlassValidation(
            ref=ref,
            override_id=override_id,
            valid=True,
            reason="BreakGlassOverride is active, scoped, human-approved, unexpired, and has remaining uses.",
            audit_ref=str(spec.get("auditRef")),
            approver_ref=str(approver.get("id")),
            action_class=str(spec.get("actionClass")),
            resource=str(spec.get("resource")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return BreakGlassValidation(ref=ref, valid=False, reason=f"BreakGlassOverride validation failed: {exc}")


def make_check(
    check_id: str,
    name: str,
    result: str,
    required: bool,
    reason: str | None = None,
    remediation: str | None = None,
    evidence_refs: list[str] | None = None,
    policy_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "checkId": check_id,
        "name": name,
        "result": result,
        "required": required,
        "reason": reason,
        "remediation": remediation,
        "evidenceRefs": evidence_refs or [],
        "relatedPolicyDecisionRefs": policy_refs or [],
    }


def evaluate_checks(config: StopGateConfig, state: RepoState) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    if not state.branch:
        checks.append(make_check("branch-present", "Branch detected", "fail", True, "No Git branch could be detected.", "Run inside a Git worktree or provide branch evidence."))
    elif state.branch in config.protected_branches:
        checks.append(make_check("branch-not-protected", "Working branch is not protected", "fail", True, f"Branch '{state.branch}' is protected.", "Create a feature/workcell branch and replay the agent task there."))
    else:
        checks.append(make_check("branch-not-protected", "Working branch is not protected", "pass", True, f"Branch '{state.branch}' is not protected.", None, [f"branch:{state.branch}"]))

    if not state.commit:
        checks.append(make_check("commit-present", "Commit exists", "fail", True, "No HEAD commit could be detected.", "Commit the completed work before claiming done."))
    elif state.clean is False:
        checks.append(make_check("worktree-clean", "Worktree clean", "fail", True, "The worktree has uncommitted changes.", "Commit or intentionally discard changes before claiming done.", [f"commit:{state.commit}"]))
    elif state.clean is None:
        checks.append(make_check("worktree-clean", "Worktree clean", "fail", True, "Worktree cleanliness could not be determined.", "Collect Git status evidence and re-run the stop gate.", [f"commit:{state.commit}"]))
    else:
        checks.append(make_check("worktree-clean", "Worktree clean", "pass", True, "HEAD commit exists and worktree is clean.", None, [f"commit:{state.commit}"]))

    if not state.upstream:
        checks.append(make_check("branch-pushed", "Branch pushed", "fail", True, "No upstream branch evidence was found.", "Push the branch and re-run the stop gate."))
    elif state.ahead is None or state.behind is None:
        checks.append(make_check("branch-pushed", "Branch pushed", "fail", True, "Ahead/behind counts could not be determined.", "Fetch remote state and re-run the stop gate.", [f"upstream:{state.upstream}"]))
    elif state.ahead > 0:
        checks.append(make_check("branch-pushed", "Branch pushed", "fail", True, f"Branch has {state.ahead} unpushed commit(s).", "Push the branch and re-run the stop gate.", [f"upstream:{state.upstream}"]))
    elif state.behind > 0:
        checks.append(make_check("branch-current", "Branch current with upstream", "fail", True, f"Branch is behind upstream by {state.behind} commit(s).", "Rebase/merge current upstream state and re-run validation.", [f"upstream:{state.upstream}"]))
    else:
        checks.append(make_check("branch-pushed", "Branch pushed", "pass", True, "Branch is pushed and current with upstream.", None, [f"upstream:{state.upstream}"]))

    if config.require_pr:
        if state.pr_ref:
            checks.append(make_check("pull-request-present", "Pull request exists", "pass", True, "Pull request evidence is present.", None, [state.pr_ref]))
        else:
            checks.append(make_check("pull-request-present", "Pull request exists", "fail", True, "No pull request evidence was found.", "Open a pull request or provide a signed no-PR exception."))
    else:
        checks.append(make_check("pull-request-present", "Pull request exists", "not_applicable", False, "PR requirement disabled for this gate.", None))

    normalized_ci = (state.ci_status or "unknown").lower()
    if config.require_ci:
        if normalized_ci in {"success", "passed", "green"}:
            checks.append(make_check("ci-green", "CI green", "pass", True, "CI status is green.", None, ["ci:success"]))
        elif normalized_ci in {"pending", "queued", "in_progress"}:
            checks.append(make_check("ci-green", "CI green", "needs_human", True, f"CI is {normalized_ci}.", "Wait for CI to complete before claiming done.", [f"ci:{normalized_ci}"]))
        else:
            checks.append(make_check("ci-green", "CI green", "fail", True, f"CI status is {normalized_ci}.", "Fix failing or missing checks, then re-run the stop gate.", [f"ci:{normalized_ci}"]))
    else:
        checks.append(make_check("ci-green", "CI green", "not_applicable", False, "CI requirement disabled for this gate.", None))

    if config.require_summary:
        if state.summary_present:
            checks.append(make_check("summary-present", "Completion summary present", "pass", True, "Completion summary evidence is present.", None, [state.summary_ref or "summary:inline"]))
        else:
            checks.append(make_check("summary-present", "Completion summary present", "fail", True, "No completion summary evidence was found.", "Write a task summary with changed files, validation evidence, and remaining risks."))
    else:
        checks.append(make_check("summary-present", "Completion summary present", "not_applicable", False, "Summary requirement disabled for this gate.", None))

    if state.unresolved_policy_decision_refs:
        checks.append(make_check("guardrail-clear", "No unresolved blocking guardrail decisions", "fail", True, "Blocking guardrail decisions remain unresolved.", "Resolve, supersede, or obtain a signed human override for each blocking decision.", [state.decision_log_ref] if state.decision_log_ref else [], state.unresolved_policy_decision_refs))
    elif config.require_decision_log and not state.decision_log_ref:
        checks.append(make_check("guardrail-clear", "No unresolved blocking guardrail decisions", "fail", True, "No guardrail decision log evidence was provided.", "Provide a guardrail decision log or disable this requirement by policy."))
    else:
        checks.append(make_check("guardrail-clear", "No unresolved blocking guardrail decisions", "pass", True, "No unresolved blocking guardrail decisions were found.", None, [state.decision_log_ref] if state.decision_log_ref else []))

    if config.break_glass.ref:
        if config.break_glass.valid:
            checks.append(make_check("break-glass-valid", "PolicyFabric break-glass override valid", "pass", True, config.break_glass.reason, None, [config.break_glass.ref]))
        else:
            checks.append(make_check("break-glass-valid", "PolicyFabric break-glass override valid", "fail", True, config.break_glass.reason, "Provide an active, unexpired, human-approved PolicyFabric BreakGlassOverride artifact.", [config.break_glass.ref]))

    return checks


def aggregate_result(checks: list[dict[str, Any]], human_override_ref: str | None, break_glass: BreakGlassValidation) -> str:
    required_failures = [check for check in checks if check["required"] and check["result"] == "fail"]
    required_human = [check for check in checks if check["required"] and check["result"] == "needs_human"]
    invalid_break_glass = any(check["checkId"] == "break-glass-valid" and check["result"] == "fail" for check in checks)
    if invalid_break_glass:
        return "fail"
    if (human_override_ref or break_glass.valid) and (required_failures or required_human):
        return "waived"
    if required_failures:
        return "fail"
    if required_human:
        return "needs_human"
    return "pass"


def build_stop_gate_artifact(config: StopGateConfig, state: RepoState, checks: list[dict[str, Any]]) -> dict[str, Any]:
    result = aggregate_result(checks, config.human_override_ref, config.break_glass)
    summary = "Stop gate passed."
    if result == "fail":
        failed = [check["checkId"] for check in checks if check["required"] and check["result"] == "fail"]
        summary = f"Stop gate failed: {', '.join(failed)}."
    elif result == "needs_human":
        summary = "Stop gate requires human attention before completion."
    elif result == "waived":
        summary = "Stop gate failures were waived by human override or PolicyFabric break-glass override."

    return {
        "kind": "StopGateArtifact",
        "bundle": config.bundle,
        "capturedAt": utc_now(),
        "sessionRef": config.session_ref,
        "taskRef": config.task_ref,
        "gateId": config.gate_id,
        "gateName": config.gate_name,
        "gatePolicyRef": config.gate_policy_ref,
        "result": result,
        "summary": summary,
        "checks": checks,
        "humanOverrideRef": config.human_override_ref,
        "breakGlassOverrideRef": config.break_glass.ref,
        "artifactRefs": {
            "policyDecisionArtifactRefs": state.unresolved_policy_decision_refs,
            "breakGlassOverrideRef": config.break_glass.ref,
            "runArtifactRef": None,
            "replayArtifactRef": None,
            "pullRequestRef": state.pr_ref,
            "ciStatusRef": f"ci:{state.ci_status}" if state.ci_status else None,
            "summaryRef": state.summary_ref,
        },
        "governanceContext": {
            "breakGlass": {
                "overrideId": config.break_glass.override_id,
                "valid": config.break_glass.valid,
                "reason": config.break_glass.reason,
                "auditRef": config.break_glass.audit_ref,
                "approverRef": config.break_glass.approver_ref,
                "actionClass": config.break_glass.action_class,
                "resource": config.break_glass.resource,
            } if config.break_glass.ref else None
        },
    }


def evaluate_stop_gate(config: StopGateConfig, state: RepoState) -> dict[str, Any]:
    checks = evaluate_checks(config, state)
    return build_stop_gate_artifact(config, state, checks)


def build_state_from_environment(args: argparse.Namespace) -> RepoState:
    cwd = Path(args.cwd).resolve()
    git = inspect_git_state(cwd)
    pr_ref = args.pr_ref or inspect_pr_ref(cwd)
    decision_log = Path(args.decision_log).resolve() if args.decision_log else None
    unresolved = inspect_decision_log(decision_log)

    summary_ref = args.summary_ref
    summary_present: bool | None = None
    if args.summary_file:
        summary_path = Path(args.summary_file)
        summary_ref = summary_ref or str(summary_path)
        summary_present = summary_path.exists() and bool(summary_path.read_text(encoding="utf-8").strip())
    elif args.summary_inline:
        summary_ref = summary_ref or "summary:inline"
        summary_present = bool(args.summary_inline.strip())

    return RepoState(
        branch=args.branch or git["branch"],
        commit=args.commit or git["commit"],
        clean=args.clean if args.clean is not None else git["clean"],
        upstream=args.upstream or git["upstream"],
        ahead=args.ahead if args.ahead is not None else git["ahead"],
        behind=args.behind if args.behind is not None else git["behind"],
        pr_ref=pr_ref,
        ci_status=args.ci_status,
        summary_ref=summary_ref,
        summary_present=summary_present,
        unresolved_policy_decision_refs=unresolved,
        decision_log_ref=str(decision_log) if decision_log else None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate AgentPlane stop gates and emit StopGateArtifact JSON.")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--session-ref", required=True)
    parser.add_argument("--task-ref")
    parser.add_argument("--gate-id", default="sourceos.default.agent-completion")
    parser.add_argument("--gate-name", default="SourceOS Default Agent Completion Gate")
    parser.add_argument("--gate-policy-ref", default="sourceos/agentplane/default-stop-gates@0.1.0")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--protected-branch", action="append", dest="protected_branches")
    parser.add_argument("--branch")
    parser.add_argument("--commit")
    parser.add_argument("--clean", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--upstream")
    parser.add_argument("--ahead", type=int)
    parser.add_argument("--behind", type=int)
    parser.add_argument("--pr-ref")
    parser.add_argument("--no-require-pr", action="store_true")
    parser.add_argument("--ci-status")
    parser.add_argument("--no-require-ci", action="store_true")
    parser.add_argument("--summary-file")
    parser.add_argument("--summary-inline")
    parser.add_argument("--summary-ref")
    parser.add_argument("--no-require-summary", action="store_true")
    parser.add_argument("--decision-log")
    parser.add_argument("--require-decision-log", action="store_true")
    parser.add_argument("--human-override-ref")
    parser.add_argument("--break-glass-override", help="Path to PolicyFabric BreakGlassOverride artifact")
    parser.add_argument("--out", help="Path to write StopGateArtifact JSON. Defaults to stdout only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    protected = tuple(args.protected_branches or DEFAULT_PROTECTED_BRANCHES)
    break_glass = validate_break_glass_override(Path(args.break_glass_override).resolve() if args.break_glass_override else None)
    config = StopGateConfig(
        bundle=args.bundle,
        session_ref=args.session_ref,
        task_ref=args.task_ref,
        gate_id=args.gate_id,
        gate_name=args.gate_name,
        gate_policy_ref=args.gate_policy_ref,
        protected_branches=protected,
        require_pr=not args.no_require_pr,
        require_ci=not args.no_require_ci,
        require_summary=not args.no_require_summary,
        require_decision_log=args.require_decision_log,
        human_override_ref=args.human_override_ref,
        break_glass=break_glass,
    )
    state = build_state_from_environment(args)
    artifact = evaluate_stop_gate(config, state)

    encoded = json.dumps(artifact, indent=2, sort_keys=True)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if artifact["result"] in {"pass", "waived"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
