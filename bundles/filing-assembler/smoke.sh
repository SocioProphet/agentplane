#!/usr/bin/env bash
set -euo pipefail

echo "[banking-twin] smoke start: filing-assembler"
echo "[banking-twin] purpose: Evidence-bound filing-pack assembly for regulatory and management outputs."

test -d /mnt/artifacts || mkdir -p /mnt/artifacts
printf '%s\n' "filing-assembler" > /mnt/artifacts/bundle-name.txt
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /mnt/artifacts/smoke-ran-at.txt
echo "[banking-twin] smoke ok"
