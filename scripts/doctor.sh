#!/usr/bin/env bash
set -euo pipefail

echo "[doctor] agentplane preflight"

TARGET_SYSTEM="${1:-aarch64-linux}"

command -v nix >/dev/null || { echo "[doctor] FAIL: nix not in PATH"; exit 2; }

BUILDERS="$(nix config show 2>/dev/null | awk -F" = " '/^builders =/ {print $2}' | head -n1)"

HOST_SYS="$(uname -s | tr '[:upper:]' '[:lower:]')"
if [[ "${HOST_SYS}" == "darwin" && "${TARGET_SYSTEM}" == *"-linux" ]]; then
  if [[ -z "${BUILDERS// /}" ]]; then
    echo "[doctor] FAIL: building ${TARGET_SYSTEM} on macOS requires a remote Linux builder, but nix.builders is empty." >&2
    echo "[doctor] Next: pick a reachable Linux host, install Nix there, then set builders = ssh-ng://user@host ..." >&2
    exit 2
  fi
fi

if [[ "${BUILDERS}" == *"<"* || "${BUILDERS}" == *"BUILDER_"* ]]; then
  echo "[doctor] FAIL: nix.builders contains placeholder text: ${BUILDERS}" >&2
  echo "[doctor] Fix: set builders to a real ssh-ng://user@host ..." >&2
  exit 2
fi

echo "[doctor] OK"
