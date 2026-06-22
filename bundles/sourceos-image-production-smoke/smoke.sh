#!/usr/bin/env bash
set -euo pipefail

echo "[sourceos-image-production-smoke] validating SourceOS image-production bundle wiring"

BUNDLE_PATH="${AGENTPLANE_BUNDLE_PATH:-bundles/sourceos-image-production-smoke/bundle.json}"

test -n "${BUNDLE_PATH}"
test -f "${BUNDLE_PATH}"

echo "[sourceos-image-production-smoke] bundle path: ${BUNDLE_PATH}"

AGENTPLANE_ROOT="${AGENTPLANE_ROOT:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo ".")}"
python3 "${AGENTPLANE_ROOT}/tools/validate_sourceos_bundle.py" --bundle "${BUNDLE_PATH}"

echo "[sourceos-image-production-smoke] smoke complete"
