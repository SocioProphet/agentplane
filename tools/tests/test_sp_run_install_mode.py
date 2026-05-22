from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentplane_cli import sp_run as entrypoint  # noqa: E402


def test_sp_run_entrypoint_loads_source_checkout_delegate() -> None:
    module = entrypoint._load_tool_module()

    assert hasattr(module, "main")
    assert entrypoint._tool_path().exists()


def test_sp_run_install_error_payload_is_structured(tmp_path: Path) -> None:
    missing_root = tmp_path / "installed-package"
    missing_tool = missing_root / "tools" / "sp_run.py"
    err = entrypoint.SpRunInstallError(missing_root, missing_tool)

    payload = err.as_payload()
    assert payload["recordType"] == "SpRunInstallError"
    assert payload["ok"] is False
    assert payload["mode"] == "source_checkout_required"
    assert payload["tool_path"] == str(missing_tool)
    assert "editable" in payload["resolution"]
    assert "agent_execution" in payload["non_goals"]


def test_sp_run_main_returns_127_when_delegate_missing(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing_root = tmp_path / "installed-package"
    monkeypatch.setattr(entrypoint, "_repo_root", lambda: missing_root)

    rc = entrypoint.main()

    captured = capsys.readouterr()
    assert rc == 127
    payload = json.loads(captured.err)
    assert payload["recordType"] == "SpRunInstallError"
    assert payload["ok"] is False
    assert payload["mode"] == "source_checkout_required"
