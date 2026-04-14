#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ALLOWED_BACKENDS = {"qemu", "microvm", "lima-process", "fleet"}
ALLOWED_HEALTH = {"ready", "degraded", "drained", "offline"}


def die(msg: str, code: int = 2) -> None:
    print(f"[validate-fleet] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"invalid json at {path}: {exc}", 2)


def require(obj: dict, key: str, path: str) -> object:
    if key not in obj:
        die(f"missing required field: {path}.{key}", 2)
    return obj[key]


def validate_node(node: dict, path: str) -> None:
    require(node, "name", path)
    require(node, "sshRef", path)
    require(node, "enabled", path)
    platform = require(node, "platform", path)
    require(platform, "os", f"{path}.platform")
    require(platform, "arch", f"{path}.platform")
    health = require(node, "health", path)
    state = require(health, "state", f"{path}.health")
    if state not in ALLOWED_HEALTH:
        die(f"invalid {path}.health.state: {state}", 2)
    require(node, "trustZone", path)
    backends = node.get("supportedBackends") or []
    for backend in backends:
        if backend not in ALLOWED_BACKENDS:
            die(f"invalid backend in {path}.supportedBackends: {backend}", 2)


def main() -> int:
    if len(sys.argv) != 2:
        die("usage: scripts/validate_fleet.py <fleet/inventory.json>", 2)

    inv_path = Path(sys.argv[1])
    if not inv_path.exists():
        die(f"missing inventory file: {inv_path}", 2)

    inv = load_json(inv_path)
    if inv.get("apiVersion") != "agentplane.socioprophet.org/v0.1":
        die("apiVersion must be agentplane.socioprophet.org/v0.1", 2)
    if inv.get("kind") != "FleetInventory":
        die("kind must be FleetInventory", 2)

    md = require(inv, "metadata", "inventory")
    for key in ("name", "version", "createdAt"):
        require(md, key, "inventory.metadata")

    builders = require(inv, "builders", "inventory")
    executors = require(inv, "executors", "inventory")
    if not isinstance(builders, list) or not builders:
        die("builders must be a non-empty array", 2)
    if not isinstance(executors, list) or not executors:
        die("executors must be a non-empty array", 2)

    builder_names = set()
    executor_names = set()
    for idx, node in enumerate(builders):
        validate_node(node, f"inventory.builders[{idx}]")
        name = node["name"]
        if name in builder_names:
            die(f"duplicate builder name: {name}", 2)
        builder_names.add(name)
    for idx, node in enumerate(executors):
        validate_node(node, f"inventory.executors[{idx}]")
        name = node["name"]
        if name in executor_names:
            die(f"duplicate executor name: {name}", 2)
        executor_names.add(name)

    default_builder = require(inv, "defaultBuilder", "inventory")
    default_executor = require(inv, "defaultExecutor", "inventory")
    if default_builder not in builder_names:
        die(f"defaultBuilder '{default_builder}' not present in builders", 2)
    if default_executor not in executor_names:
        die(f"defaultExecutor '{default_executor}' not present in executors", 2)

    selection = require(inv, "selectionPolicy", "inventory")
    for key in ("preferHealthy", "requireEnabled"):
        require(selection, key, "inventory.selectionPolicy")

    print(f"[validate-fleet] OK: {inv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
