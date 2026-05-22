#!/usr/bin/env python3
"""Read-only sp-run CLI for governed-run evidence inspection.

This v0 CLI exposes operator-facing receipt inspection only. It does not run
agents, execute verifier commands, mutate files, restore rollback state, or
change authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_run_dossier
import validate_run_dossier

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "schemas/runs/governed-run-contract.v0.1.schema.json",
    "schemas/runs/run-dossier.v0.1.schema.json",
    "schemas/receipts/attempt-admission-receipt.v0.1.schema.json",
    "schemas/receipts/rollback-boundary.v0.1.schema.json",
    "schemas/receipts/rollback-result.v0.1.schema.json",
    "tools/build_run_dossier.py",
    "tools/validate_run_dossier.py",
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_doctor(_args: argparse.Namespace) -> int:
    files = []
    ok = True
    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        ok = ok and exists
        files.append({"path": rel, "exists": exists})
    emit(
        {
            "tool": "sp-run",
            "mode": "readonly",
            "ok": ok,
            "repo_root": str(ROOT),
            "capabilities": ["doctor", "dossier", "validate-dossier"],
            "non_goals": ["execute", "mutate", "restore", "authority_update"],
            "files": files,
        }
    )
    return 0 if ok else 1


def command_dossier(args: argparse.Namespace) -> int:
    try:
        dossier = build_run_dossier.build(Path(args.run_dir), args.generated_at)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(dossier, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def command_validate_dossier(args: argparse.Namespace) -> int:
    try:
        validate_run_dossier.validate_schema(validate_run_dossier.load_json(validate_run_dossier.SCHEMA))
        validate_run_dossier.validate_dossier(validate_run_dossier.load_json(Path(args.dossier_json)))
    except Exception as exc:  # noqa: BLE001 - command boundary should report any validation failure.
        emit({"ok": False, "dossier": args.dossier_json, "error": str(exc)})
        return 1
    emit({"ok": True, "dossier": args.dossier_json})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sp-run")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check read-only governed-run evidence tooling.")
    doctor.set_defaults(func=command_doctor)

    dossier = subparsers.add_parser("dossier", help="Build a RunDossier from a governed run folder.")
    dossier.add_argument("run_dir")
    dossier.add_argument("--generated-at")
    dossier.add_argument("--output")
    dossier.set_defaults(func=command_dossier)

    validate = subparsers.add_parser("validate-dossier", help="Validate a RunDossier JSON file.")
    validate.add_argument("dossier_json")
    validate.set_defaults(func=command_validate_dossier)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
