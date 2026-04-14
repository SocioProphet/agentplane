#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_BUNDLE = REPO_ROOT / "policy/imports/control-matrix/compiled_policy_bundle_v3.json"


class ControlGateError(RuntimeError):
    """Raised when the imported control matrix cannot be evaluated safely."""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _bundle_name(bundle: dict[str, Any]) -> str:
    md = bundle.get("metadata") or {}
    return f"{md.get('name', 'UNKNOWN')}@{md.get('version', 'UNKNOWN')}"


def _pick_override(overrides: dict[str, Any], key: str, default: Any) -> Any:
    if key in overrides:
        return overrides[key]
    return default


def _stringish(value: Any, default: str = "") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _boolish_str(value: Any, default: str = "false") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower()


def derive_gate_context(bundle: dict[str, Any]) -> dict[str, str]:
    spec = bundle.get("spec") or {}
    policy = spec.get("policy") or {}
    control_matrix = policy.get("controlMatrix") or {}
    overrides = control_matrix.get("context") or {}
    abstract_reasoning = policy.get("abstractReasoning") or {}

    lane = str(policy.get("lane") or overrides.get("environment_tier") or "staging")
    env = {"dev": "dev", "staging": "staging", "prod": "prod"}.get(lane, "dev")
    phase = {"dev": "stabilize", "staging": "harden", "prod": "operate"}[env]

    human_gate_required = bool(policy.get("humanGateRequired", False))
    break_glass = bool(policy.get("breakGlass", False))

    if break_glass:
        authority = "emergency_override"
        approval_mode = "break_glass"
    elif env == "dev":
        authority = "draft"
        approval_mode = "dual_control"
    elif env == "staging":
        authority = "constrained_action"
        approval_mode = "dual_control"
    else:
        authority = "constrained_action" if human_gate_required else "autonomous"
        approval_mode = "dual_control"

    tenant_scope = "global" if bool(policy.get("globalDeployment", False)) else "single_tenant"

    reasoning_class = _stringish(
        _pick_override(overrides, "reasoning_class", abstract_reasoning.get("reasoningClass")),
        "REACTIVE",
    )
    verification_mode = _stringish(
        _pick_override(overrides, "verification_mode", abstract_reasoning.get("verificationMode")),
        "NONE",
    )
    llm_only_forbidden = _boolish_str(
        _pick_override(overrides, "llm_only_forbidden", abstract_reasoning.get("llmOnlyForbidden", False))
    )
    requires_counterexample_search = _boolish_str(
        _pick_override(
            overrides,
            "requires_counterexample_search",
            abstract_reasoning.get("requiresCounterexampleSearch", False),
        )
    )
    requires_program_candidate = _boolish_str(
        _pick_override(
            overrides,
            "requires_program_candidate",
            abstract_reasoning.get("requiresProgramCandidate", False),
        )
    )
    requires_backtracking_capability = _boolish_str(
        _pick_override(
            overrides,
            "requires_backtracking_capability",
            abstract_reasoning.get("requiresBacktrackingCapability", False),
        )
    )
    program_candidate_ref_present = _boolish_str(bool(abstract_reasoning.get("programCandidateRef")))
    counterexample_refs_present = _boolish_str(bool(abstract_reasoning.get("counterexampleRefs")))
    backtracking_capable = _boolish_str(abstract_reasoning.get("backtrackingCapable", False))

    context = {
        "phase": str(overrides.get("phase") or phase),
        "authority": str(overrides.get("authority") or authority),
        "environment_tier": str(overrides.get("environment_tier") or env),
        "approval_mode": str(overrides.get("approval_mode") or approval_mode),
        "tenant_scope": str(overrides.get("tenant_scope") or tenant_scope),
        "enforcement_point": str(overrides.get("enforcement_point") or "policy_engine"),
        "reasoning_class": reasoning_class,
        "verification_mode": verification_mode,
        "llm_only_forbidden": llm_only_forbidden,
        "requires_counterexample_search": requires_counterexample_search,
        "requires_program_candidate": requires_program_candidate,
        "requires_backtracking_capability": requires_backtracking_capability,
        "program_candidate_ref_present": program_candidate_ref_present,
        "counterexample_refs_present": counterexample_refs_present,
        "backtracking_capable": backtracking_capable,
    }
    return context


def evaluate_bundle_gate(
    bundle: dict[str, Any],
    bundle_path: Path,
    policy_bundle_path: Path | None = None,
) -> dict[str, Any]:
    policy_bundle_path = policy_bundle_path or DEFAULT_POLICY_BUNDLE
    if not policy_bundle_path.exists():
        raise ControlGateError(f"policy bundle missing: {policy_bundle_path}")

    context = derive_gate_context(bundle)

    if context["reasoning_class"] in {"ABSTRACT", "PROGRAM_INDUCTION"}:
        bundle_sha256 = hashlib.sha256(policy_bundle_path.read_bytes()).hexdigest()
        base_artifact = {
            "kind": "ControlGateArtifact",
            "bundle": _bundle_name(bundle),
            "bundlePath": str(bundle_path.resolve()),
            "evaluatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "enforcementPoint": context["enforcement_point"],
            "policyBundlePath": str(policy_bundle_path),
            "policyBundleSha256": bundle_sha256,
            "gateContext": context,
            "matchedRowIds": [],
            "blockingRowIds": [],
            "candidateRowIds": [],
        }
        if context["llm_only_forbidden"] == "true" and context["verification_mode"] == "NONE":
            return {
                **base_artifact,
                "result": "deny",
                "reason": "abstract lane forbids llm-only evaluation",
            }
        if context["requires_program_candidate"] == "true" and context["program_candidate_ref_present"] != "true":
            return {
                **base_artifact,
                "result": "deny",
                "reason": "abstract lane requires program candidate evidence",
            }
        if context["requires_counterexample_search"] == "true" and context["counterexample_refs_present"] != "true":
            return {
                **base_artifact,
                "result": "deny",
                "reason": "abstract lane requires counterexample search evidence",
            }
        if context["requires_backtracking_capability"] == "true" and context["backtracking_capable"] != "true":
            return {
                **base_artifact,
                "result": "deny",
                "reason": "abstract lane requires declared backtracking capability",
            }

    rows = _load_json(policy_bundle_path)
    relevant_rows = [
        row for row in rows if row.get("enforcement_point") == context["enforcement_point"]
    ]

    def matches(row: dict[str, Any]) -> bool:
        allow_if = row.get("allow_if") or {}
        for key in ("phase", "authority", "environment_tier", "approval_mode", "tenant_scope"):
            if allow_if.get(key) != context[key]:
                return False
        for key in (
            "reasoning_class",
            "verification_mode",
            "llm_only_forbidden",
            "requires_counterexample_search",
            "requires_program_candidate",
            "requires_backtracking_capability",
        ):
            if key in allow_if and _stringish(allow_if.get(key)).lower() != _stringish(context[key]).lower():
                return False
        return True

    exact_rows = [row for row in relevant_rows if matches(row)]
    partial_rows = [
        row
        for row in relevant_rows
        if (row.get("allow_if") or {}).get("phase") == context["phase"]
        and (row.get("allow_if") or {}).get("environment_tier") == context["environment_tier"]
    ]

    blocker_rows = [row for row in exact_rows if row.get("ship_blocker") == "BLOCK"]
    if blocker_rows:
        result = "deny"
        reason = "matched blocking policy row"
    elif exact_rows:
        result = "allow"
        reason = "matched policy row"
    else:
        result = "deny"
        reason = "no exact matching policy row"

    bundle_sha256 = hashlib.sha256(policy_bundle_path.read_bytes()).hexdigest()
    artifact = {
        "kind": "ControlGateArtifact",
        "bundle": _bundle_name(bundle),
        "bundlePath": str(bundle_path.resolve()),
        "evaluatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "result": result,
        "reason": reason,
        "enforcementPoint": context["enforcement_point"],
        "policyBundlePath": str(policy_bundle_path),
        "policyBundleSha256": bundle_sha256,
        "gateContext": context,
        "matchedRowIds": [row["row_id"] for row in exact_rows],
        "blockingRowIds": [row["row_id"] for row in blocker_rows],
        "candidateRowIds": [row["row_id"] for row in partial_rows[:12]],
    }
    return artifact


def write_gate_artifact(artifact: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the imported control matrix policy gate.")
    parser.add_argument("bundle_json", help="Path to bundle.json")
    parser.add_argument(
        "--policy-bundle",
        default=str(DEFAULT_POLICY_BUNDLE),
        help="Path to compiled_policy_bundle_v3.json",
    )
    parser.add_argument(
        "--artifact-path",
        default=None,
        help="Optional explicit output path for the control gate artifact",
    )
    args = parser.parse_args()

    bundle_path = Path(args.bundle_json)
    bundle = _load_json(bundle_path)
    artifact = evaluate_bundle_gate(bundle, bundle_path, Path(args.policy_bundle))

    out_path = (
        Path(args.artifact_path)
        if args.artifact_path
        else Path(bundle["spec"]["artifacts"]["outDir"]) / "control-gate-artifact.json"
    )
    write_gate_artifact(artifact, out_path)
    print(f"[control-gate] {artifact['result'].upper()}: wrote {out_path}")
    if artifact["result"] != "allow":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())