#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

BRANCH="${1:-}"
MSG="${2:-}"
shift 2 || true

if [[ -z "${BRANCH}" || -z "${MSG}" ]]; then
  echo "usage: scripts/pr.sh <branch-name> <commit-message> [paths...]" >&2
  exit 2
fi

# Guard: refuse to run if there are nested git repos (prevents submodule/gitlink accidents)
if find . -mindepth 2 -maxdepth 6 -name .git -type d | grep -q .; then
  echo "[error] nested .git directories detected under repo root; refuse to 'git add' blindly" >&2
  find . -mindepth 2 -maxdepth 6 -name .git -type d >&2
  exit 3
fi

./scripts/hygiene.sh

# Create branch if missing; otherwise just checkout
if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git checkout "${BRANCH}"
else
  git checkout -b "${BRANCH}"
fi

# Safer staging:
# - if paths provided, stage only those
# - else stage tracked changes only (no new untracked surprises)
if [[ "$#" -gt 0 ]]; then
  git add -- "$@"
else
  git add -u
fi

git commit -m "${MSG}"
git push -u origin "${BRANCH}"

gh pr create --base main --head "${BRANCH}" --title "${MSG}" --body "${MSG}"
