#!/usr/bin/env python3
"""Read-only governed-run evidence store inspection helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import build_run_dossier


def load_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def receipt_files(run_dir: Path) -> list[str]:
    return sorted(
        str(path.relative_to(run_dir))
        for path in run_dir.rglob("*.json")
        if path.is_file()
    )


def find_run_dirs(runs_root: Path) -> list[Path]:
    if not runs_root.exists():
        return []
    direct = [
        path
        for path in runs_root.iterdir()
        if path.is_dir() and (path / "governed-run-contract.json").exists()
    ]
    if direct:
        return sorted(direct)
    if (runs_root / "governed-run-contract.json").exists():
        return [runs_root]
    return []


def status_for_run(run_dir: Path) -> dict[str, Any]:
    dossier = build_run_dossier.build(run_dir)
    return {
        "recordType": "RunStatus",
        "run_id": dossier["run_id"],
        "run_dir": str(run_dir),
        "overall_status": dossier["overall_status"],
        "attempt_count": dossier["attempt_count"],
        "latest_admission": dossier["latest_admission"],
        "latest_rollback": dossier["latest_rollback"],
        "budget_summary": dossier["budget_summary"],
        "missing_receipts": dossier["missing_receipts"],
        "recommended_next_action": dossier["recommended_next_action"],
    }


def list_runs(runs_root: Path) -> dict[str, Any]:
    run_dirs = find_run_dirs(runs_root)
    runs: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        try:
            status = status_for_run(run_dir)
            runs.append(
                {
                    "run_id": status["run_id"],
                    "run_dir": str(run_dir),
                    "overall_status": status["overall_status"],
                    "attempt_count": status["attempt_count"],
                    "missing_receipts": status["missing_receipts"],
                }
            )
        except Exception as exc:  # noqa: BLE001 - inspection should surface malformed run dirs.
            runs.append(
                {
                    "run_id": "unknown-run",
                    "run_dir": str(run_dir),
                    "overall_status": "incomplete",
                    "attempt_count": 0,
                    "missing_receipts": ["inspection_error"],
                    "error": str(exc),
                }
            )
    return {
        "recordType": "RunList",
        "runs_root": str(runs_root),
        "count": len(runs),
        "runs": runs,
    }


def inspect_run(run_dir: Path) -> dict[str, Any]:
    dossier = build_run_dossier.build(run_dir)
    return {
        "recordType": "RunInspection",
        "run_id": dossier["run_id"],
        "run_dir": str(run_dir),
        "dossier": dossier,
        "receipt_files": receipt_files(run_dir),
        "non_goals": [
            "agent_execution",
            "verifier_execution",
            "file_mutation",
            "rollback_restore",
            "authority_update",
            "budget_settlement",
        ],
    }
