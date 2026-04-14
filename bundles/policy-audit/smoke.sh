#!/usr/bin/env bash
set -euo pipefail

echo "[banking-twin] smoke start: policy-audit"
echo "[banking-twin] purpose: Policy and control-matrix audit bundle for banking twin runs."

test -d /mnt/artifacts || mkdir -p /mnt/artifacts
printf '%s\n' "policy-audit" > /mnt/artifacts/bundle-name.txt
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /mnt/artifacts/smoke-ran-at.txt
echo "[banking-twin] smoke ok"
