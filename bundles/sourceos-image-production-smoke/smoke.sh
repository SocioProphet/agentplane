#!/usr/bin/env bash
set -euo pipefail

echo "[sourceos-image-production-smoke] validating SourceOS image-production bundle wiring"

test -n "${AGENTPLANE_BUNDLE_PATH:-bundles/sourceos-image-production-smoke/bundle.json}"
test -f "${AGENTPLANE_BUNDLE_PATH:-bundles/sourceos-image-production-smoke/bundle.json}"

echo "[sourceos-image-production-smoke] bundle path: ${AGENTPLANE_BUNDLE_PATH:-bundles/sourceos-image-production-smoke/bundle.json}"
echo "[sourceos-image-production-smoke] smoke complete"
