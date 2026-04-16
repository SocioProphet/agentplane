#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts/sourceos-asahi-stage

if [ ! -d /mnt/config ]; then
  echo "missing /mnt/config" >&2
  exit 1
fi

if [ ! -d /mnt/evidence ]; then
  echo "missing /mnt/evidence" >&2
  exit 1
fi

cat > artifacts/sourceos-asahi-stage/smoke-result.json <<'JSON'
{
  "bundle": "sourceos-asahi-stage",
  "status": "ok"
}
JSON

echo "sourceos-asahi-stage smoke passed"
