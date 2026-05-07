#!/usr/bin/env bash
set -euo pipefail

# Evidence-aware wrapper around qemu-local.sh.
#
# This runner path delegates execution to the existing qemu-local runner and then,
# when postcondition inputs are present, emits typed postcondition/divergence
# evidence through scripts/emit_execution_evidence_artifacts.py.
#
# It is intentionally additive. It does not rewrite qemu-local.sh and it does not
# hand-author canonical JSON.

AP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QEMU_LOCAL="${AP_ROOT}/runners/qemu-local.sh"
EVIDENCE_EMITTER="${AP_ROOT}/scripts/emit_execution_evidence_artifacts.py"

if [[ ! -x "${QEMU_LOCAL}" ]]; then
  echo "[qemu-local-evidence] ERROR: missing runner: ${QEMU_LOCAL}" >&2
  exit 2
fi

if [[ ! -f "${EVIDENCE_EMITTER}" ]]; then
  echo "[qemu-local-evidence] ERROR: missing evidence emitter: ${EVIDENCE_EMITTER}" >&2
  exit 2
fi

cmd="${1:-}"
bundle_dir="${2:-}"

"${QEMU_LOCAL}" "$@"
rc=$?

# Only run postcondition/divergence emission for successful run commands. Other
# commands such as smoke/promote/rollback/status/stop keep their existing shape.
if [[ "${cmd}" != "run" || "${rc}" != "0" ]]; then
  exit "${rc}"
fi

if [[ -z "${bundle_dir}" || ! -d "${bundle_dir}" ]]; then
  echo "[qemu-local-evidence] WARN: bundle dir unavailable; skipping execution evidence" >&2
  exit "${rc}"
fi

bundle_json="${bundle_dir%/}/bundle.json"
if [[ ! -f "${bundle_json}" ]]; then
  echo "[qemu-local-evidence] WARN: bundle.json unavailable; skipping execution evidence" >&2
  exit "${rc}"
fi

# These inputs are intentionally env-driven so callers can decide whether a run
# has enough planner/postcondition context to emit evidence.
if [[ -z "${PLANNER_EXPECTED_STATE_HASH:-}" || -z "${OBSERVED_STATE_HASH:-}" ]]; then
  echo "[qemu-local-evidence] INFO: postcondition hashes not set; skipping execution evidence"
  exit "${rc}"
fi

run_artifact_ref="${RUN_ARTIFACT_REF:-agentplane://run-artifact/run-artifact.json}"
comparison_result="${POSTCONDITION_RESULT:-UNKNOWN}"

cmd_args=(
  "${bundle_json}"
  "${run_artifact_ref}"
  --expected-state-hash "${PLANNER_EXPECTED_STATE_HASH}"
  --observed-state-hash "${OBSERVED_STATE_HASH}"
  --comparison-result "${comparison_result}"
)

if [[ -n "${MATCHED_CONDITIONS:-}" ]]; then
  IFS=',' read -r -a matched_conditions <<< "${MATCHED_CONDITIONS}"
  for condition in "${matched_conditions[@]}"; do
    [[ -n "${condition}" ]] && cmd_args+=(--matched-condition "${condition}")
  done
fi

if [[ -n "${FAILED_CONDITIONS:-}" ]]; then
  IFS=',' read -r -a failed_conditions <<< "${FAILED_CONDITIONS}"
  for condition in "${failed_conditions[@]}"; do
    [[ -n "${condition}" ]] && cmd_args+=(--failed-condition "${condition}")
  done
fi

if [[ -n "${EVIDENCE_REFS:-}" ]]; then
  IFS=',' read -r -a evidence_refs <<< "${EVIDENCE_REFS}"
  for evidence in "${evidence_refs[@]}"; do
    [[ -n "${evidence}" ]] && cmd_args+=(--evidence-ref "${evidence}")
  done
fi

if [[ -n "${DIVERGENCE_CLASS:-}" ]]; then
  cmd_args+=(--divergence-class "${DIVERGENCE_CLASS}")
  cmd_args+=(--expected-ref "${EXPECTED_REF:?EXPECTED_REF is required when DIVERGENCE_CLASS is set}")
  cmd_args+=(--observed-ref "${OBSERVED_REF:?OBSERVED_REF is required when DIVERGENCE_CLASS is set}")
  cmd_args+=(--divergence-severity "${DIVERGENCE_SEVERITY:-HIGH}")
  [[ -n "${POLICY_IMPACT:-}" ]] && cmd_args+=(--policy-impact "${POLICY_IMPACT}")
  [[ -n "${INCIDENT_REF:-}" ]] && cmd_args+=(--incident-ref "${INCIDENT_REF}")
  if [[ "${REPLAN_REQUIRED:-false}" == "true" ]]; then
    cmd_args+=(--replan-required)
  fi
fi

python3 "${EVIDENCE_EMITTER}" "${cmd_args[@]}"
exit "${rc}"
