#!/usr/bin/env python3
"""Validate AgentPlane GuardedWorkcellArtifact schema and sample artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "guarded-workcell-artifact.schema.v0.1.json"
PLANNER = ROOT / "tools" / "plan_guarded_workcell.py"


def die(message: str) -> None:
    print(f"[guarded-workcell] ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        die(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path}: {exc}")
    if not isinstance(data, dict):
        die(f"expected JSON object in {path}")
    return data


def require_keys(obj: dict[str, Any], keys: list[str], path: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        die(f"{path} missing keys: {missing}")


def require_schema_shape(schema: dict[str, Any]) -> None:
    require_keys(schema, ["$schema", "title", "type", "required", "properties"], "GuardedWorkcellArtifact schema")
    require_keys(
        {key: True for key in schema.get("required") or []},
        [
            "kind",
            "bundle",
            "capturedAt",
            "sessionRef",
            "taskRef",
            "repo",
            "baseRef",
            "worktree",
            "guardrail",
            "stopGate",
            "runtime",
            "result",
            "sideEffects",
        ],
        "GuardedWorkcellArtifact.required",
    )

    properties = schema.get("properties") or {}
    result_enum = ((properties.get("result") or {}).get("enum") or [])
    for value in ["planned", "ready", "blocked", "needs_human"]:
        if value not in result_enum:
            die(f"GuardedWorkcellArtifact.result enum missing {value}")


def run_planner(args: list[str]) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(PLANNER), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        die(f"planner did not emit JSON: {exc}; stdout={completed.stdout!r}; stderr={completed.stderr!r}")
    return completed.returncode, data


def validate_sample_artifact(artifact: dict[str, Any]) -> None:
    require_keys(
        artifact,
        [
            "kind",
            "bundle",
            "capturedAt",
            "sessionRef",
            "taskRef",
            "repo",
            "baseRef",
            "worktree",
            "guardrail",
            "stopGate",
            "runtime",
            "result",
            "sideEffects",
        ],
        "sample GuardedWorkcellArtifact",
    )
    if artifact["kind"] != "GuardedWorkcellArtifact":
        die("sample artifact kind must be GuardedWorkcellArtifact")
    if artifact["sideEffects"] != {
        "gitWorktreeCreated": False,
        "branchCreated": False,
        "externalMutationPerformed": False,
        "agentInvoked": False,
    }:
        die("planner must remain side-effect free")


def main() -> int:
    schema = load_json(SCHEMA)
    require_schema_shape(schema)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "guarded-workcell-artifact.json"
        code, artifact = run_planner(
            [
                "--bundle",
                "example-agent@0.1.0",
                "--repo",
                "SocioProphet/agentplane",
                "--base-ref",
                "main",
                "--task-ref",
                "urn:srcos:task:validate-workcell",
                "--session-ref",
                "urn:srcos:session:validate-workcell",
                "--branch",
                "work/validate-workcell",
                "--strategy",
                "plan-only",
                "--base-commit",
                "abc123",
                "--remote",
                "https://github.com/SocioProphet/agentplane.git",
                "--out",
                str(out),
            ]
        )
        if code != 0:
            die(f"expected planned artifact exit code 0, got {code}: {artifact}")
        validate_sample_artifact(artifact)
        if artifact["result"] != "planned":
            die(f"expected result=planned, got {artifact['result']}")
        if not out.exists():
            die("expected --out artifact to be written")

        code, blocked = run_planner(
            [
                "--bundle",
                "example-agent@0.1.0",
                "--repo",
                "SocioProphet/agentplane",
                "--base-ref",
                "main",
                "--task-ref",
                "urn:srcos:task:blocked-workcell",
                "--session-ref",
                "urn:srcos:session:blocked-workcell",
                "--branch",
                "work/blocked-workcell",
                "--allow-side-effects",
            ]
        )
        if code == 0:
            die(f"side-effect permission posture should not pass the plan-only gate: {blocked}")
        if blocked["result"] != "blocked":
            die(f"expected side-effect posture result=blocked, got {blocked['result']}")

    print("[guarded-workcell] OK: guarded workcell artifact validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
