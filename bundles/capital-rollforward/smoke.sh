#!/usr/bin/env bash
set -euo pipefail

echo "[banking-twin] smoke start: capital-rollforward"
echo "[banking-twin] purpose: Capital and ratio roll-forward execution over projected banking state."

test -d /mnt/artifacts || mkdir -p /mnt/artifacts
printf '%s\n' "capital-rollforward" > /mnt/artifacts/bundle-name.txt
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /mnt/artifacts/smoke-ran-at.txt
echo "[banking-twin] smoke ok"
