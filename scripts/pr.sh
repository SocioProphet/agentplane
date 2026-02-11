#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

BRANCH="${1:-}"
MSG="${2:-}"
if [[ -z "${BRANCH}" || -z "${MSG}" ]]; then
  echo "usage: scripts/pr.sh <branch-name> <commit-message>" >&2
  exit 2
fi

./scripts/hygiene.sh

git checkout -b "${BRANCH}"
git add -A
git commit -m "${MSG}"
git push -u origin "${BRANCH}"

gh pr create --repo SocioProphet/agentplane --base main --head "${BRANCH}" --title "${MSG}" --body "${MSG}"
