"""Installed entry point for the AgentPlane sp-run CLI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_tool_module():
    tool_path = _repo_root() / "tools" / "sp_run.py"
    spec = importlib.util.spec_from_file_location("agentplane_tools_sp_run", tool_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load sp-run implementation from {tool_path}")
    module = importlib.util.module_from_spec(spec)
    tools_dir = str(tool_path.parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = _load_tool_module()
    return int(module.main(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
