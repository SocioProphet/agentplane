#!/usr/bin/env python3
"""Capture a RollbackBoundary receipt for the current repo state.

The tool is read-only: it inspects git state and snapshots changed file content
as base64 evidence. It does not mutate the workspace.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_rel_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or "/../" in normalized
    ):
        raise ValueError(f"unsafe repo-relative path: {path!r}")
    return normalized


def git_lines(args: list[str], repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    return sorted({safe_rel_path(line) for line in result.stdout.splitlines() if line.strip()})


def git_scalar(args: list[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return "unavailable"
    return result.stdout.strip() or "unavailable"


def read_snapshot(repo_root: Path, rel_path: str) -> dict[str, Any]:
    safe = safe_rel_path(rel_path)
    absolute = (repo_root / safe).resolve()
    root = repo_root.resolve()
    if root not in absolute.parents and absolute != root:
        raise ValueError(f"refusing path outside repo root: {safe}")
    if not absolute.exists() or not absolute.is_file():
        return {"path": safe, "existed": False, "encoding": "base64"}
    return {
        "path": safe,
        "existed": True,
        "encoding": "base64",
        "content_base64": base64.b64encode(absolute.read_bytes()).decode("ascii"),
    }


def stable_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_boundary(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    tracked = git_lines(["diff", "--name-only", "HEAD"], repo_root)
    untracked = git_lines(["ls-files", "--others", "--exclude-standard"], repo_root)
    snapshot_paths = sorted(set(tracked + untracked))
    captured_at = args.captured_at or now_utc()
    record: dict[str, Any] = {
        "schemaVersion": "agentplane.rollback-boundary.v0.1",
        "recordType": "RollbackBoundary",
        "boundary_id": args.boundary_id,
        "run_id": args.run_id,
        "attempt_id": args.attempt_id,
        "repo_root": args.repo_root,
        "captured_at": captured_at,
        "strategy": "git_head_plus_snapshot",
        "head_ref": git_scalar(["rev-parse", "HEAD"], repo_root),
        "tracked_dirty_files": tracked,
        "untracked_files": untracked,
        "snapshots": [read_snapshot(repo_root, path) for path in snapshot_paths],
    }
    record["receipt_hash"] = stable_hash(record)
    return record


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--boundary-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--captured-at")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        record = build_boundary(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    data = json.dumps(record, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(data, encoding="utf-8")
    else:
        print(data, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
