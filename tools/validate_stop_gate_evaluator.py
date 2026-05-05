#!/usr/bin/env python3
"""Deterministic smoke validation for the SourceOS stop gate evaluator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "tools" / "evaluate_stop_gate.py"


def die(message: str) -> None:
    print(f"[stop-gate] ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def run_eval(args: list[str]) -> tuple[int, dict]:
    completed = subprocess.run(
        [sys.executable, str(EVALUATOR), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        die(f"evaluator did not emit JSON: {exc}; stdout={completed.stdout!r}; stderr={completed.stderr!r}")
    return completed.returncode, data


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        summary = Path(tmp) / "summary.md"
        summary.write_text("validation summary\n", encoding="utf-8")
        decision_log = Path(tmp) / "guardrail-decisions.jsonl"
        decision_log.write_text(
            json.dumps({"decisionId": "allow-1", "decision": "allow", "severity": "info"}) + "\n",
            encoding="utf-8",
        )
        out = Path(tmp) / "stop-gate-artifact.json"

        code, artifact = run_eval(
            [
                "--bundle",
                "example-agent@0.1.0",
                "--session-ref",
                "urn:srcos:session:validate-stop-gate",
                "--task-ref",
                "urn:srcos:task:validate-stop-gate",
                "--cwd",
                str(ROOT),
                "--branch",
                "work/validated",
                "--commit",
                "abc123",
                "--clean",
                "--upstream",
                "origin/work/validated",
                "--ahead",
                "0",
                "--behind",
                "0",
                "--pr-ref",
                "https://github.com/SocioProphet/agentplane/pull/0",
                "--ci-status",
                "success",
                "--summary-file",
                str(summary),
                "--decision-log",
                str(decision_log),
                "--out",
                str(out),
            ]
        )
        if code != 0:
            die(f"expected pass exit code 0, got {code}: {artifact}")
        if artifact.get("kind") != "StopGateArtifact" or artifact.get("result") != "pass":
            die(f"unexpected passing artifact: {artifact}")
        if not out.exists():
            die("expected --out artifact to be written")

        code, failing = run_eval(
            [
                "--bundle",
                "example-agent@0.1.0",
                "--session-ref",
                "urn:srcos:session:validate-stop-gate-fail",
                "--cwd",
                str(ROOT),
                "--branch",
                "main",
                "--commit",
                "abc123",
                "--clean",
                "--upstream",
                "origin/main",
                "--ahead",
                "0",
                "--behind",
                "0",
                "--ci-status",
                "failure",
                "--no-require-pr",
                "--no-require-summary",
            ]
        )
        if code == 0:
            die(f"expected failing gate to return non-zero: {failing}")
        if failing.get("result") != "fail":
            die(f"expected failing gate result=fail: {failing}")

    print("[stop-gate] OK: stop gate evaluator smoke validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
