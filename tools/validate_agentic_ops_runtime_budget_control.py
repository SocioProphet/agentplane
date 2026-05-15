#!/usr/bin/env python3
"""Validate Agentic Ops runtime budget control contracts.

Stdlib-only validator for the v0.1 schema/example tranche. It checks
contract presence and invariants that JSON Schema does not express cleanly.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCHEMAS = {
    "persona": ROOT / "schemas" / "agentic-ops-persona-policy.schema.v0.1.json",
    "workload": ROOT / "schemas" / "agentic-ops-workload-signature.schema.v0.1.json",
    "budget": ROOT / "schemas" / "agentic-ops-budget-ledger.schema.v0.1.json",
    "trajectory": ROOT / "schemas" / "agentic-ops-trajectory-event.schema.v0.1.json",
}

EXAMPLES = {
    "regulated_persona": ROOT / "examples" / "agentic-ops" / "regulated-persona-policy.example.json",
    "research_persona": ROOT / "examples" / "agentic-ops" / "research-persona-policy.example.json",
    "workload": ROOT / "examples" / "agentic-ops" / "regulated-workload-signature.example.json",
    "budget": ROOT / "examples" / "agentic-ops" / "budget-ledger.example.json",
    "trajectory": ROOT / "examples" / "agentic-ops" / "trajectory-event.example.json",
}

OBJECTIVE_KEYS = [
    "latency",
    "throughput",
    "costPredictability",
    "correctness",
    "auditability",
    "opsSimplicity",
    "reproducibility",
    "collaboration",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing {rel(path)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"expected JSON object in {rel(path)}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_kind(data: dict[str, Any], kind: str, name: str) -> None:
    require(data.get("apiVersion") == "agentplane.socioprophet.org/v0.1", f"{name}: apiVersion mismatch")
    require(data.get("kind") == kind, f"{name}: kind mismatch")


def validate_schema_headers() -> None:
    expected = {
        "persona": ("Agentic Ops Persona Policy", "AgenticOpsPersonaPolicy"),
        "workload": ("Agentic Ops Workload Signature", "AgenticOpsWorkloadSignature"),
        "budget": ("Agentic Ops Budget Ledger", "AgenticOpsBudgetLedger"),
        "trajectory": ("Agentic Ops Trajectory Event", "AgenticOpsTrajectoryEvent"),
    }
    for key, path in SCHEMAS.items():
        schema = load(path)
        title, kind = expected[key]
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{rel(path)}: schema draft mismatch")
        require(schema.get("title") == title, f"{rel(path)}: schema title mismatch")
        actual_kind = schema.get("properties", {}).get("kind", {}).get("const")
        require(actual_kind == kind, f"{rel(path)}: kind const mismatch")


def objective_sum(persona: dict[str, Any]) -> float:
    objectives = persona["spec"]["objectives"]
    return sum(float(objectives[k]) for k in OBJECTIVE_KEYS)


def validate_persona(path: Path, *, allow_unrestricted: bool) -> dict[str, Any]:
    persona = load(path)
    require_kind(persona, "AgenticOpsPersonaPolicy", rel(path))
    require(abs(objective_sum(persona) - 1.0) < 1e-9, f"{rel(path)}: objective weights must sum to 1.0")

    thresholds = persona["spec"]["budgetDefaults"]["degradationThresholds"]
    require(
        thresholds["warnRatio"] <= thresholds["degradeRatio"] <= thresholds["hardStopRatio"],
        f"{rel(path)}: degradation thresholds must be ordered",
    )

    allowlist = set(persona["spec"]["dataClassAllowlist"])
    require(allowlist, f"{rel(path)}: data class allowlist is empty")

    reversibility = persona["spec"]["agenticAxes"]["reversibility"]
    if not allow_unrestricted:
        require(reversibility != "unrestricted", f"{rel(path)}: regulated persona cannot permit unrestricted reversibility")
        require("regulated" in allowlist, f"{rel(path)}: regulated persona must admit regulated data")
        require(persona["spec"]["agenticAxes"]["planMode"] == "plan_then_execute", f"{rel(path)}: regulated persona must be plan_then_execute")
        require(persona["spec"]["agenticAxes"]["verificationJudgeRate"] == 1.0, f"{rel(path)}: regulated persona must verify every output")

    return persona


def validate_workload(path: Path, regulated_persona: dict[str, Any]) -> None:
    workload = load(path)
    require_kind(workload, "AgenticOpsWorkloadSignature", rel(path))
    data_class = workload["spec"]["dataClass"]
    require(data_class in regulated_persona["spec"]["dataClassAllowlist"], f"{rel(path)}: workload data class not admitted by regulated persona")
    require(workload["spec"]["expectedTrajectoryLength"] >= 1, f"{rel(path)}: expected trajectory length must be positive")
    require("make validate" in workload["spec"]["expectedValidationCommands"], f"{rel(path)}: expected validation must include make validate")


def validate_budget(path: Path) -> None:
    budget = load(path)
    require_kind(budget, "AgenticOpsBudgetLedger", rel(path))
    spec = budget["spec"]
    require(spec["admissionDecision"] in {"admit", "reject", "admit_with_degradation"}, f"{rel(path)}: invalid admission decision")

    for dim, cap_value in spec["caps"].items():
        observed = spec["observed"][dim]
        remaining = spec["remaining"][dim]
        require(observed + remaining <= cap_value + 1e-9, f"{rel(path)}: observed + remaining exceeds cap for {dim}")

    refs = set(spec["policyRefs"])
    require(any(ref.startswith("policy-fabric://") for ref in refs), f"{rel(path)}: missing Policy Fabric ref")
    require(any(ref.startswith("guardrail-fabric://") for ref in refs), f"{rel(path)}: missing Guardrail Fabric ref")


def canonical_event_hash(event: dict[str, Any]) -> str:
    clone = copy.deepcopy(event)
    clone["spec"]["hashes"]["eventHash"] = "sha256:" + ("0" * 64)
    payload = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_trajectory(path: Path) -> None:
    event = load(path)
    require_kind(event, "AgenticOpsTrajectoryEvent", rel(path))
    hashes = event["spec"]["hashes"]
    require(hashes["previousEventHash"].startswith("sha256:"), f"{rel(path)}: missing previous event hash")
    require(hashes["eventHash"].startswith("sha256:"), f"{rel(path)}: missing event hash")
    require(hashes["eventHash"] == canonical_event_hash(event), f"{rel(path)}: event hash mismatch")

    cache = event["spec"]["cache"]
    if cache["cacheablePrefixTokens"] == 0:
        require(cache["cacheHitRatio"] == 0, f"{rel(path)}: cache hit ratio must be zero without cacheable prefix")
    else:
        expected_ratio = cache["cacheHitTokens"] / cache["cacheablePrefixTokens"]
        require(abs(expected_ratio - cache["cacheHitRatio"]) < 1e-9, f"{rel(path)}: cache hit ratio mismatch")


def main() -> int:
    validate_schema_headers()
    regulated = validate_persona(EXAMPLES["regulated_persona"], allow_unrestricted=False)
    validate_persona(EXAMPLES["research_persona"], allow_unrestricted=True)
    validate_workload(EXAMPLES["workload"], regulated)
    validate_budget(EXAMPLES["budget"])
    validate_trajectory(EXAMPLES["trajectory"])
    print("OK: validated Agentic Ops runtime budget control contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
