#!/usr/bin/env python3
"""Record a RollbackResult receipt by comparing repo state to a boundary.

This tool is non-mutating. It reads git state and an existing RollbackBoundary
receipt, then emits a RollbackResult receipt describing whether the current
state matches the recorded boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def current_state(repo_root: Path) -> dict[str, list[str]]:
    return {
        "tracked_dirty_files": git_lines(["diff", "--name-only", "HEAD"], repo_root),
        "untracked_files": git_lines(["ls-files", "--others", "--exclude-standard"], repo_root),
    }


def stable_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_boundary(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("boundary file must contain a JSON object")
    if data.get("recordType") != "RollbackBoundary":
        raise ValueError("boundary file must have recordType=RollbackBoundary")
    return data


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    boundary = load_boundary(Path(args.boundary))
    before = {
        "tracked_dirty_files": list(boundary.get("tracked_dirty_files", [])),
        "untracked_files": list(boundary.get("untracked_files", [])),
    }
    after = current_state(repo_root)
    matches = before == after
    attempted = bool(args.attempted)
    if matches and attempted:
        status = "restored"
    elif matches:
        status = "not_required"
    else:
        status = "failed" if attempted else "unavailable"
    changed_paths = sorted(set(before["tracked_dirty_files"] + before["untracked_files"] + after["tracked_dirty_files"] + after["untracked_files"]))
    record: dict[str, Any] = {
        "schemaVersion": "agentplane.rollback-result.v0.1",
        "recordType": "RollbackResult",
        "result_id": args.result_id,
        "boundary_ref": boundary["boundary_id"],
        "run_id": args.run_id or boundary["run_id"],
        "attempt_id": args.attempt_id or boundary["attempt_id"],
        "attempted": attempted,
        "status": status,
        "recorded_at": args.recorded_at or now_utc(),
        "before": before,
        "after": after,
        "changed_paths": changed_paths,
    }
    if status in {"failed", "unavailable"}:
        record["error"] = "current repo state does not match the recorded rollback boundary"
    record["receipt_hash"] = stable_hash(record)
    return record


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--boundary", required=True)
    parser.add_argument("--result-id", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--attempt-id")
    parser.add_argument("--recorded-at")
    parser.add_argument("--attempted", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        record = build_result(args)
    except (ValueError, json.JSONDecodeError) as exc:
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
