#!/usr/bin/env bash
set -euo pipefail

echo "[banking-twin] smoke start: stress-runner"
echo "[banking-twin] purpose: Scenario-conditioned stress execution over a GAIA banking twin snapshot."

test -d /mnt/artifacts || mkdir -p /mnt/artifacts
printf '%s\n' "stress-runner" > /mnt/artifacts/bundle-name.txt
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /mnt/artifacts/smoke-ran-at.txt
echo "[banking-twin] smoke ok"
