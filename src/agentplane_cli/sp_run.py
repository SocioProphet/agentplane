"""Installed entry point for the AgentPlane sp-run CLI.

The v0 package entry point delegates to the source-checkout implementation under
`tools/sp_run.py`. That is intentional until the governed-runner implementation
is promoted into importable package modules. If the entry point is invoked from a
non-source install where `tools/sp_run.py` is unavailable, it fails closed with a
clear diagnostic instead of raising an opaque import error.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


class SpRunInstallError(RuntimeError):
    """Raised when the source-checkout delegate is unavailable."""

    def __init__(self, repo_root: Path, tool_path: Path):
        self.repo_root = repo_root
        self.tool_path = tool_path
        super().__init__(f"sp-run source delegate is unavailable: {tool_path}")

    def as_payload(self) -> dict[str, Any]:
        return {
            "recordType": "SpRunInstallError",
            "ok": False,
            "mode": "source_checkout_required",
            "repo_root": str(self.repo_root),
            "tool_path": str(self.tool_path),
            "message": "sp-run currently requires an AgentPlane source or editable checkout with tools/sp_run.py present.",
            "resolution": "Run from a SocioProphet/agentplane checkout or install AgentPlane in editable mode with python3 -m pip install -e .",
            "non_goals": [
                "agent_execution",
                "verifier_execution",
                "governed_workspace_mutation",
                "rollback_restore",
                "authority_update",
                "budget_settlement",
            ],
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _tool_path() -> Path:
    return _repo_root() / "tools" / "sp_run.py"


def _load_tool_module():
    tool_path = _tool_path()
    if not tool_path.exists():
        raise SpRunInstallError(_repo_root(), tool_path)
    spec = importlib.util.spec_from_file_location("agentplane_tools_sp_run", tool_path)
    if spec is None or spec.loader is None:
        raise SpRunInstallError(_repo_root(), tool_path)
    module = importlib.util.module_from_spec(spec)
    tools_dir = str(tool_path.parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    try:
        module = _load_tool_module()
    except SpRunInstallError as exc:
        print(json.dumps(exc.as_payload(), indent=2, sort_keys=True), file=sys.stderr)
        return 127
    return int(module.main(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
