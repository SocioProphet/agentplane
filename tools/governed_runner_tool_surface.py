#!/usr/bin/env python3
"""Read-only governed-runner tool surface adapter.

This is a local JSON tool adapter for governed-runner inspection workflows. It
reuses AgentPlane-owned sp-run helpers and intentionally exposes only read-only
operations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

import build_run_dossier
import run_governed_runner_smoke
import run_store_inspection
import sp_run
import validate_run_dossier

TOOL_NAMES = (
    "governed_runner.doctor",
    "governed_runner.smoke",
    "governed_runner.list",
    "governed_runner.status",
    "governed_runner.inspect",
    "governed_runner.dossier",
    "governed_runner.validate_dossier",
    "governed_runner.preflight",
    "governed_runner.admit",
)

NON_GOALS = (
    "agent_execution",
    "verifier_execution",
    "governed_workspace_mutation",
    "rollback_restore",
    "authority_update",
    "budget_settlement",
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def tool_descriptor(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "mode": "readonly",
        "owner": "SocioProphet/agentplane",
        "non_goals": list(NON_GOALS),
    }


def list_tools() -> dict[str, Any]:
    return {
        "recordType": "GovernedRunnerToolList",
        "tools": [tool_descriptor(name) for name in TOOL_NAMES],
    }


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    table: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
        "governed_runner.doctor": call_doctor,
        "governed_runner.smoke": call_smoke,
        "governed_runner.list": call_list,
        "governed_runner.status": call_status,
        "governed_runner.inspect": call_inspect,
        "governed_runner.dossier": call_dossier,
        "governed_runner.validate_dossier": call_validate_dossier,
        "governed_runner.preflight": call_preflight,
        "governed_runner.admit": call_admit,
    }
    if name not in table:
        raise ValueError(f"unknown governed-runner tool: {name}")
    return table[name](args)


def call_doctor(_args: dict[str, Any]) -> dict[str, Any]:
    return {
        "recordType": "GovernedRunnerToolDoctor",
        "ok": True,
        "mode": "readonly",
        "tools": list(TOOL_NAMES),
        "non_goals": list(NON_GOALS),
    }


def call_smoke(args: dict[str, Any]) -> dict[str, Any]:
    output_dir = Path(str(args.get("output_dir", ".socioprophet/smoke/governed-runner")))
    generated_at = str(args.get("generated_at", "2026-05-22T12:45:00Z"))
    return run_governed_runner_smoke.build_smoke(output_dir, generated_at)


def call_list(args: dict[str, Any]) -> dict[str, Any]:
    return run_store_inspection.list_runs(Path(str(args.get("runs_root", ".socioprophet/runs"))))


def call_status(args: dict[str, Any]) -> dict[str, Any]:
    return run_store_inspection.status_for_run(Path(require_arg(args, "run_dir")))


def call_inspect(args: dict[str, Any]) -> dict[str, Any]:
    return run_store_inspection.inspect_run(Path(require_arg(args, "run_dir")))


def call_dossier(args: dict[str, Any]) -> dict[str, Any]:
    generated_at = args.get("generated_at")
    return build_run_dossier.build(Path(require_arg(args, "run_dir")), None if generated_at is None else str(generated_at))


def call_validate_dossier(args: dict[str, Any]) -> dict[str, Any]:
    dossier_path = Path(require_arg(args, "dossier_json"))
    try:
        validate_run_dossier.validate_schema(validate_run_dossier.load_json(validate_run_dossier.SCHEMA))
        validate_run_dossier.validate_dossier(validate_run_dossier.load_json(dossier_path))
    except Exception as exc:  # noqa: BLE001 - tool boundary returns structured validation failure.
        return {"recordType": "GovernedRunnerDossierValidation", "ok": False, "error": str(exc)}
    return {"recordType": "GovernedRunnerDossierValidation", "ok": True, "dossier": str(dossier_path)}


def call_preflight(args: dict[str, Any]) -> dict[str, Any]:
    contract = load_object(Path(require_arg(args, "contract_json")))
    generated_at = args.get("generated_at")
    return sp_run.build_preflight_receipt(contract, None if generated_at is None else str(generated_at))


def call_admit(args: dict[str, Any]) -> dict[str, Any]:
    contract = load_object(Path(require_arg(args, "contract_json")))
    preflight = load_object(Path(require_arg(args, "preflight_json")))
    authority = load_object(Path(require_arg(args, "authority_state_json")))
    projected_cost = float(args.get("projected_cost_usd", 0.0))
    generated_at = args.get("generated_at")
    return sp_run.build_attempt_admission_receipt(
        contract,
        preflight,
        authority,
        projected_cost_usd=projected_cost,
        generated_at=None if generated_at is None else str(generated_at),
    )


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def require_arg(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required argument: {key}")
    return value


def parse_args_json(value: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--args-json must be a JSON object")
    return parsed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-tools")

    call = sub.add_parser("call")
    call.add_argument("tool_name")
    call.add_argument("--args-json", default="{}")

    args = parser.parse_args(argv)
    try:
        if args.command == "list-tools":
            emit(list_tools())
            return 0
        emit(call_tool(args.tool_name, parse_args_json(args.args_json)))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        emit({"recordType": "GovernedRunnerToolError", "ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
