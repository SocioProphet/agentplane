#!/usr/bin/env bash
set -euo pipefail

echo "[doctor] agentplane preflight"

command -v nix >/dev/null || { echo "[doctor] FAIL: nix not in PATH"; exit 2; }

BUILDERS="$(nix config show 2>/dev/null | awk -F" = " '/^builders =/ {print $2}' | head -n1)"

if [[ "${BUILDERS}" == *"<"* || "${BUILDERS}" == *"BUILDER_"* ]]; then
  echo "[doctor] FAIL: nix.builders contains placeholder text: ${BUILDERS}" >&2
  echo "[doctor] Fix: set builders to a real ssh-ng://user@host ..." >&2
  exit 2
fi

echo "[doctor] OK"
