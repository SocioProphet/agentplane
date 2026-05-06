from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

MODULE_PATH = TOOLS_DIR / "create_guarded_workcell.py"
spec = importlib.util.spec_from_file_location("create_guarded_workcell", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["create_guarded_workcell"] = module
spec.loader.exec_module(module)

main = module.main


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "agentplane@example.invalid")
    run_git(repo, "config", "user.name", "AgentPlane Test")
    (repo / "README.md").write_text("# test\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "initial")
    return repo


def base_args(repo: Path, workspace: Path) -> list[str]:
    return [
        "--bundle",
        "example-agent@0.1.0",
        "--repo",
        "SocioProphet/agentplane",
        "--base-ref",
        "main",
        "--task-ref",
        "urn:srcos:task:test",
        "--session-ref",
        "urn:srcos:session:test",
        "--branch",
        "work/test-workcell",
        "--cwd",
        str(repo),
        "--workspace-path",
        str(workspace),
        "--base-commit",
        "abc123",
        "--remote",
        "https://github.com/SocioProphet/agentplane.git",
    ]


def test_executor_blocks_without_side_effect_authority(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    repo = init_repo(tmp_path)
    workspace = tmp_path / "workcell"

    exit_code = main(base_args(repo, workspace))
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 2
    assert artifact["result"] == "blocked"
    assert artifact["worktree"]["status"] == "not_created"
    assert artifact["sideEffects"]["gitWorktreeCreated"] is False
    assert not workspace.exists()


def test_executor_blocks_protected_branch(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    repo = init_repo(tmp_path)
    workspace = tmp_path / "workcell"
    args = base_args(repo, workspace)
    args[args.index("--branch") + 1] = "main"

    exit_code = main([*args, "--allow-side-effects"])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 2
    assert artifact["result"] == "blocked"
    assert artifact["sideEffects"]["gitWorktreeCreated"] is False
    assert "protected" in (artifact["governanceContext"]["reason"] or "")


def test_executor_creates_worktree_and_branch_with_authority(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    repo = init_repo(tmp_path)
    workspace = tmp_path / "workcell"
    out = tmp_path / "artifact.json"

    exit_code = main([*base_args(repo, workspace), "--allow-side-effects", "--out", str(out)])
    captured = capsys.readouterr()
    stdout_artifact = json.loads(captured.out)
    file_artifact = json.loads(out.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout_artifact["result"] == "ready"
    assert stdout_artifact["worktree"]["status"] == "created"
    assert stdout_artifact["sideEffects"]["gitWorktreeCreated"] is True
    assert stdout_artifact["sideEffects"]["branchCreated"] is True
    assert stdout_artifact["sideEffects"]["agentInvoked"] is False
    assert file_artifact["sessionRef"] == stdout_artifact["sessionRef"]
    assert workspace.exists()
    assert (workspace / "README.md").exists()
    assert run_git(repo, "rev-parse", "--verify", "work/test-workcell").stdout.strip()


def test_executor_binds_existing_workspace_without_mutation(tmp_path, capsys) -> None:  # type: ignore[no-untyped-def]
    repo = init_repo(tmp_path)
    workspace = tmp_path / "existing-workcell"
    workspace.mkdir()

    exit_code = main([*base_args(repo, workspace), "--strategy", "existing", "--allow-side-effects"])
    captured = capsys.readouterr()
    artifact = json.loads(captured.out)

    assert exit_code == 0
    assert artifact["result"] == "ready"
    assert artifact["worktree"]["status"] == "existing"
    assert artifact["sideEffects"]["gitWorktreeCreated"] is False
    assert artifact["sideEffects"]["branchCreated"] is False
