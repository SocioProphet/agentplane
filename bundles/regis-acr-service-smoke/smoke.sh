#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-./artifacts/regis-acr-service-smoke}"
mkdir -p "$OUT_DIR"

cat > "$OUT_DIR/regis-acr-smoke-summary.json" <<JSON
{
  "kind": "RegisAcrServiceSmokeSummary",
  "bundle": "regis-acr-service-smoke@0.1.0",
  "service": "regis-acr-api",
  "createdAt": "$(date -Iseconds)",
  "checks": [
    {"name": "health", "status": "planned", "endpoint": "GET /healthz"},
    {"name": "source_record_ingest", "status": "planned", "endpoint": "POST /v1/source-records"},
    {"name": "concordance_proposal", "status": "planned", "endpoint": "POST /v1/concordance/proposals"},
    {"name": "promotion_low_margin_block", "status": "planned", "endpoint": "POST /v1/promotion/evaluate"},
    {"name": "relationship_formation_hook", "status": "planned", "endpoint": "POST /v1/relationships/formation-hooks"}
  ],
  "safetyPosture": {
    "canonicalMutation": false,
    "externalEgress": false,
    "inlineSecrets": false,
    "evidenceFirst": true,
    "ontogenesisActivation": false
  },
  "notes": "Bootstrap bundle writes a smoke summary artifact. Prophet Platform smoke target should replace planned checks with live endpoint assertions once wired."
}
JSON

cat > "$OUT_DIR/placement-receipt.json" <<JSON
{
  "kind": "PlacementReceipt",
  "bundle": "regis-acr-service-smoke@0.1.0",
  "decision": {
    "chosenSite": "local-host",
    "backend": "lima-process",
    "constraints": { "networkMode": "nat", "lane": "staging", "egress": "dns-only" },
    "rejectedSites": [],
    "objective": { "note": "fixture-backed service smoke; no external egress" }
  },
  "signedBy": "UNSET",
  "createdAt": "$(date -Iseconds)"
}
JSON

echo "[regis-acr-service-smoke] wrote artifacts to $OUT_DIR"
