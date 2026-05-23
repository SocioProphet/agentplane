#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "chains" / "governed-runner-v0.2-contract-chain.valid.json"

REQUIRED_ARTIFACTS = {
    "authority_state",
    "safety_handoff",
    "governed_run_contract",
    "attempt_admission",
    "verification_receipt",
    "budget_settlement",
    "run_dossier",
}

REQUIRED_EDGES = {
    ("authority_state", "attempt_admission", "authority_input"),
    ("safety_handoff", "attempt_admission", "safety_input"),
    ("governed_run_contract", "attempt_admission", "contract_input"),
    ("attempt_admission", "verification_receipt", "admission_required"),
    ("verification_receipt", "budget_settlement", "settlement_after_result"),
    ("attempt_admission", "run_dossier", "dossier_summarizes"),
    ("budget_settlement", "run_dossier", "dossier_summarizes"),
}

BLOCKED = {
    "real_verifier_runner",
    "shell_passthrough",
    "arbitrary_command_input",
    "network_activity",
    "workspace_mutation",
    "provider_invocation",
    "authority_update",
    "recovery_action",
    "budget_provider_integration",
}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        fail("expected JSON object")
    return payload


def require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def require_object(record: dict[str, Any], key: str) -> dict[str, Any]:
    value = record.get(key)
    if not isinstance(value, dict):
        fail(f"{key}: expected object")
    return value


def validate_chain(chain: dict[str, Any]) -> None:
    if chain.get("schemaVersion") != "agentplane.governed-runner-v0.2-contract-chain.v0.1":
        fail("schemaVersion mismatch")
    if chain.get("recordType") != "GovernedRunnerV02ContractChain":
        fail("recordType mismatch")
    if chain.get("mode") != "synthetic_contract_chain":
        fail("mode must be synthetic_contract_chain")
    require_string(chain, "chain_id")
    require_string(chain, "run_id")
    require_string(chain, "attempt_id")

    artifacts = require_object(chain, "artifacts")
    missing = sorted(REQUIRED_ARTIFACTS - set(artifacts))
    if missing:
        fail(f"missing artifacts: {missing}")

    authority = require_object(artifacts, "authority_state")
    if authority.get("owner") != "SocioProphet/agent-registry":
        fail("authority_state owner mismatch")
    if authority.get("status") in {"suspended", "revoked"}:
        fail("authority_state must not be suspended or revoked")

    safety = require_object(artifacts, "safety_handoff")
    if safety.get("owner") != "SocioProphet/guardrail-fabric":
        fail("safety_handoff owner mismatch")
    if safety.get("authoritative_safety_owner") != "SocioProphet/guardrail-fabric":
        fail("safety handoff must preserve authoritative owner")
    if safety.get("outcome") != "pass" or safety.get("runtime_action") != "allow":
        fail("safety handoff must pass/allow")

    contract = require_object(artifacts, "governed_run_contract")
    if contract.get("owner") != "SocioProphet/agentplane":
        fail("governed_run_contract owner mismatch")

    admission = require_object(artifacts, "attempt_admission")
    if admission.get("owner") != "SocioProphet/agentplane":
        fail("attempt_admission owner mismatch")
    if admission.get("decision") != "admit":
        fail("attempt_admission must admit")
    if admission.get("preflight_outcome") != safety.get("outcome"):
        fail("attempt_admission preflight outcome does not match safety handoff")
    if admission.get("runtime_action") != safety.get("runtime_action"):
        fail("attempt_admission runtime action does not match safety handoff")
    if admission.get("authority_decision") in {"suspended", "revoked"}:
        fail("attempt_admission authority decision cannot be suspended or revoked")

    verification = require_object(artifacts, "verification_receipt")
    if verification.get("owner") != "SocioProphet/agentplane":
        fail("verification_receipt owner mismatch")
    if verification.get("producer") != "synthetic":
        fail("verification_receipt must use synthetic producer")
    if verification.get("allowlisted") is not True:
        fail("verification receipt must be allowlisted")
    if verification.get("network_mode") != "off":
        fail("verification receipt must keep network_mode off")
    if verification.get("mutation_mode") != "none":
        fail("verification receipt must keep mutation_mode none")
    if verification.get("validates_with") != "tools/validate_verification_execution_receipt.py":
        fail("verification receipt validator ref mismatch")

    budget = require_object(artifacts, "budget_settlement")
    if budget.get("owner") != "SocioProphet/agentplane":
        fail("budget_settlement owner mismatch")
    if budget.get("status") != "settled":
        fail("budget_settlement must be settled in this fixture")
    if budget.get("over_budget") is not False:
        fail("budget_settlement must not be over budget")
    if budget.get("actual_cost_usd", 0) > budget.get("estimated_cost_usd", 0):
        fail("budget_settlement hides an overrun")

    dossier = require_object(artifacts, "run_dossier")
    if dossier.get("owner") != "SocioProphet/agentplane":
        fail("run_dossier owner mismatch")
    if dossier.get("status") != "ready":
        fail("run_dossier must be ready")

    edges = chain.get("required_edges")
    if not isinstance(edges, list):
        fail("required_edges must be a list")
    edge_set = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            fail(f"required_edges[{index}] must be object")
        edge_set.add((edge.get("from"), edge.get("to"), edge.get("relation")))
    missing_edges = sorted(REQUIRED_EDGES - edge_set)
    if missing_edges:
        fail(f"missing required edges: {missing_edges}")

    blocked = require_object(chain, "blocked_capabilities")
    for key in sorted(BLOCKED):
        if blocked.get(key) is not True:
            fail(f"blocked capability must be true: {key}")


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) == 2 else DEFAULT_FIXTURE
    try:
        validate_chain(load(path))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {path} validates as governed-runner v0.2 contract chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
