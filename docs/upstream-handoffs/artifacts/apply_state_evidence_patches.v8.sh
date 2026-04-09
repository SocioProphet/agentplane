#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 /path/to/agentplane /path/to/agentplane-recipes [--with-tests]" >&2
  exit 2
fi

AGENTPLANE_DIR="$1"
RECIPES_DIR="$2"
WITH_TESTS="${3:-}"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"

AP_PATCHES=(
  "$PATCH_DIR/agentplane-state-evidence-incidents.v2.patch"
  "$PATCH_DIR/agentplane-incidents-evidence-pack.tests.pr2.patch"
  "$PATCH_DIR/agentplane-task-explain.pr1.patch"
  "$PATCH_DIR/agentplane-task-reconcile-and-ci.pr1.patch"
  "$PATCH_DIR/agentplane-task-explain-evidence-expansion.pr2.patch"
  "$PATCH_DIR/agentplane-backend-authority-conflicts.pr3.patch"
  "$PATCH_DIR/agentplane-backend-snapshot-sync-conflicts.pr4.patch"
  "$PATCH_DIR/agentplane-backend-warning-metadata.pr5.patch"
)

RECIPES_PATCHES=(
  "$PATCH_DIR/agentplane-recipes-state-drift-lab.pr1.patch"
  "$PATCH_DIR/agentplane-recipes-state-drift-lab-integrity.pr2.patch"
)

echo "[preflight] agentplane patches"
for p in "${AP_PATCHES[@]}"; do
  git -C "$AGENTPLANE_DIR" apply --check "$p"
done

echo "[preflight] recipes patches"
for p in "${RECIPES_PATCHES[@]}"; do
  git -C "$RECIPES_DIR" apply --check "$p"
done

echo "[apply] agentplane patches"
for p in "${AP_PATCHES[@]}"; do
  git -C "$AGENTPLANE_DIR" apply --whitespace=fix "$p"
done

echo "[apply] recipes patches"
for p in "${RECIPES_PATCHES[@]}"; do
  git -C "$RECIPES_DIR" apply --whitespace=fix "$p"
done

if [[ "$WITH_TESTS" == "--with-tests" ]]; then
  echo "[tests] focused state-evidence suite"
  (
    cd "$AGENTPLANE_DIR"
    bun x vitest run \
      packages/agentplane/src/runtime/incidents/resolve.test.ts \
      packages/agentplane/src/commands/task/explain.unit.test.ts \
      packages/agentplane/src/commands/task/reconcile.unit.test.ts
  )
fi

echo "[done] state-evidence stack applied"
