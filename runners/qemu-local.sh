#!/usr/bin/env bash
set -euo pipefail

# qemu-local backend (v0): contract-first.
# Today: validate bundle, run smoke, emit artifacts, manage pointers.
# Next: build+boot NixOS VM and execute smoke inside guest (same interface).

usage() {
  cat <<USAGE
Usage:
  runners/qemu-local.sh run <bundle-dir> [--profile staging|prod]
  runners/qemu-local.sh smoke <bundle-dir>
  runners/qemu-local.sh promote <bundle-dir>
  runners/qemu-local.sh rollback
  runners/qemu-local.sh status
  runners/qemu-local.sh stop

Notes:
  - <bundle-dir> is a directory containing bundle.json
  - v0 does not boot a VM yet; it is contract+artifacts+pointers.
USAGE
}

AP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${AP_ROOT}/state"
POINTERS_DIR="${STATE_DIR}/pointers"

cmd="${1:-}"
shift || true

bundle_dir=""
profile="staging"

TARGET_SYSTEM="aarch64-linux"

if [[ "$cmd" == "run" || "$cmd" == "smoke" || "$cmd" == "promote" ]]; then
  bundle_dir="${1:-}"
  shift || true
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --profile) profile="${2:-}"; shift 2;;
      --system) TARGET_SYSTEM="${2:-}"; shift 2;;
      *) echo "[runner] unknown arg: $1" >&2; exit 2;;
    esac
  done
  if [[ -z "$bundle_dir" || ! -d "$bundle_dir" ]]; then
    echo "[runner] bundle-dir missing or not a directory" >&2
    usage; exit 2
  fi
fi

bundle_json=""
if [[ -n "$bundle_dir" ]]; then
  bundle_json="${bundle_dir%/}/bundle.json"
  [[ -f "$bundle_json" ]] || { echo "[runner] missing $bundle_json" >&2; exit 2; }
fi

read_json_field() {
  # minimal JSON reader: python stdlib only
  local file="$1" field="$2"
  python3 - <<PY
import json
b=json.load(open("$file","r",encoding="utf-8"))
cur=b
for k in "$field".split("."):
    cur=cur[k]
print(cur)
PY
}

ensure_pointers() {
  mkdir -p "$POINTERS_DIR"
  touch "${POINTERS_DIR}/current-staging" "${POINTERS_DIR}/current-prod" "${POINTERS_DIR}/previous-good"
}

emit_run_artifact() {
  local out_dir="$1" bundle_name="$2" bundle_ver="$3" lane="$4"
  mkdir -p "$out_dir"
  cat > "${out_dir}/run-artifact.json" <<JSON
{
  "kind": "RunArtifact",
  "bundle": "${bundle_name}@${bundle_ver}",
  "lane": "${lane}",
  "backend": "qemu-local",
  "startedAt": "$(date -Iseconds)",
  "endedAt": "$(date -Iseconds)",
  "result": "pass",
  "notes": "v0 runner: smoke executed on host. Next: smoke executed inside guest VM."
}
JSON
}

emit_placement_receipt() {
  local out_dir="$1" bundle_name="$2" bundle_ver="$3" lane="$4"
  mkdir -p "$out_dir"
  cat > "${out_dir}/placement-receipt.json" <<JSON
{
  "kind": "PlacementReceipt",
  "bundle": "${bundle_name}@${bundle_ver}",
  "decision": {
    "chosenSite": "local-host",
    "backend": "qemu-local",
    "constraints": { "lane": "${lane}" },
    "rejectedSites": []
  },
  "signedBy": "UNSET",
  "createdAt": "$(date -Iseconds)"
}
JSON
}

case "$cmd" in
  run)
    # Host prerequisites (fail fast, product-grade)
    command -v python3 >/dev/null || { echo "[runner] ERROR: python3 is required" >&2; exit 2; }
    command -v nix >/dev/null || {
      echo "[runner] ERROR: nix is required for VM builds (nix command not found)." >&2
      echo "[runner] Hint: install Nix on this host, or run this backend on a Linux host with Nix." >&2
      exit 2
    }
    ensure_pointers
    echo "[runner] validate bundle..."
    "${AP_ROOT}/scripts/validate_bundle.py" "$bundle_json" >/dev/null

    name="$(read_json_field "$bundle_json" "metadata.name")"
    ver="$(read_json_field "$bundle_json" "metadata.version")"
    out_dir="$(read_json_field "$bundle_json" "spec.artifacts.outDir")"
    smoke_script="$(read_json_field "$bundle_json" "spec.smoke.script")"

    echo "[runner] build VM artifact (flake package vm-example-agent)..."
    HOST_SYS="$(uname -s | tr '[:upper:]' '[:lower:]')"
    if [[ "${HOST_SYS}" == "darwin" && "${TARGET_SYSTEM}" == *"-linux" ]]; then
      # On macOS we need a remote Linux builder; building Linux closures locally is not available.
      BUILDERS="$(nix config show 2>/dev/null | awk -F" = " '/^builders =/ {print $2}' | head -n1 | tr -d ' ')"
      if [[ -z "${BUILDERS}" ]]; then
        echo "[runner] ERROR: target system ${TARGET_SYSTEM} requires a remote Linux builder, but nix.builders is empty." >&2
        echo "[runner] Remediation: set builders = ssh-ng://user@<linux-host> ${TARGET_SYSTEM} ... in /etc/nix/nix.conf" >&2
        echo "[runner] This is expected on hotspot/NAT networks with no reachable Linux host." >&2
        exit 2
      fi
    fi
    HOST_SYS="$(uname -s | tr '[:upper:]' '[:lower:]')"
    if [[ "${HOST_SYS}" == "darwin" && "${TARGET_SYSTEM}" == *"-linux" ]]; then
      # On macOS we need a remote Linux builder; building Linux closures locally is not available.
      BUILDERS="$(nix config show 2>/dev/null | awk -F" = " '/^builders =/ {print $2}' | head -n1 | tr -d ' ')"
      if [[ -z "${BUILDERS}" ]]; then
        echo "[runner] ERROR: target system ${TARGET_SYSTEM} requires a remote Linux builder, but nix.builders is empty." >&2
        echo "[runner] Remediation: set builders = ssh-ng://user@<linux-host> ${TARGET_SYSTEM} ... in /etc/nix/nix.conf" >&2
        echo "[runner] This is expected on hotspot/NAT networks with no reachable Linux host." >&2
        exit 2
      fi
    fi
    # Build VM artifact. On Linux, add --extra-experimental-features if needed.
    nix build ".#packages.${TARGET_SYSTEM}.vm-example-agent" --no-link

    # Find the VM run script from the build output
    VM_OUT="$(nix path-info ".#packages.${TARGET_SYSTEM}.vm-example-agent")"
    RUN_SCRIPT="$(ls -1 "${VM_OUT}"/bin/run-*-vm 2>/dev/null | head -n1 || true)"
    if [[ -z "${RUN_SCRIPT}" ]]; then
      echo "[runner] ERROR: could not find run-*-vm script in ${VM_OUT}/bin" >&2
      exit 2
    fi

    echo "[runner] run VM (guest executes smoke and powers off)..."
    mkdir -p "${AP_ROOT}/${out_dir}"

    # If we are on macOS and the target is Linux, we must run the VM on Linux too.
    if [[ "${HOST_SYS}" == "darwin" && "${TARGET_SYSTEM}" == *"-linux" ]]; then
      REMOTE="lima-nixbuilder"
      REMOTE_ROOT="/tmp/agentplane-run"
      ssh "${REMOTE}" "mkdir -p ${REMOTE_ROOT}/repo ${REMOTE_ROOT}/artifacts"
      echo "[runner] darwin->linux: delegating build+run to ${REMOTE} (rsync repo + artifacts, run QEMU there, sync artifacts back)"

      # Sync repo (excluding runtime artifacts) to remote
      rsync -a --delete --exclude ".git/" --exclude "artifacts/" --exclude "state/pointers/" "${AP_ROOT}/" "${REMOTE}:${REMOTE_ROOT}/repo/"

      # Sync artifacts dir to remote (so QEMU can mount it)
      rsync -a "${AP_ROOT}/${out_dir}/" "${REMOTE}:${REMOTE_ROOT}/artifacts/" || true

      # Build+run inside remote Linux
      ssh "${REMOTE}" "set -euo pipefail; \
        . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh; \
        cd ${REMOTE_ROOT}/repo; \
        nix build .#packages.${TARGET_SYSTEM}.vm-example-agent --no-link; \
        VM_OUT=\"$(nix path-info .#packages.${TARGET_SYSTEM}.vm-example-agent)\"; \
        RUN_SCRIPT=\"$(ls -1 ${VM_OUT}/bin/run-*-vm | head -n1)\"; \
        mkdir -p ${REMOTE_ROOT}/artifacts; \
        export QEMU_OPTS=\"${QEMU_OPTS:-} -virtfs local,path=${REMOTE_ROOT}/artifacts,mount_tag=artifacts,security_model=none,id=artifacts -nographic -serial mon:stdio\"; \
        ${RUN_SCRIPT} >/dev/null"

      # Sync artifacts back
      rsync -a --delete "${REMOTE}:${REMOTE_ROOT}/artifacts/" "${AP_ROOT}/${out_dir}/"

      echo "[runner] emit placement receipt (host-side scheduling receipt)..."
    else
      # Local Linux host path
      export QEMU_OPTS="${QEMU_OPTS:-} -virtfs local,path=${AP_ROOT}/${out_dir},mount_tag=artifacts,security_model=none,id=artifacts"
      "${RUN_SCRIPT}" >/dev/null
      echo "[runner] emit placement receipt (host-side scheduling receipt)..."
    fi
    emit_placement_receipt "${AP_ROOT}/${out_dir}" "$name" "$ver" "$profile"
    echo "[runner] NOTE: run-artifact.json should now be guest-authored in ${out_dir}"

    echo "[runner] update current-${profile} pointer..."
    printf '%s\n' "${bundle_dir%/}" > "${POINTERS_DIR}/current-${profile}"

    echo "[runner] OK: ${name}@${ver} (${profile})"
    ;;

  smoke)
    echo "[runner] validate bundle..."
    "${AP_ROOT}/scripts/validate_bundle.py" "$bundle_json" >/dev/null
    out_dir="$(read_json_field "$bundle_json" "spec.artifacts.outDir")"
    smoke_script="$(read_json_field "$bundle_json" "spec.smoke.script")"
    "${AP_ROOT}/${smoke_script}" "${AP_ROOT}/${out_dir}"
    ;;

  promote)
    ensure_pointers
    "${AP_ROOT}/scripts/validate_bundle.py" "$bundle_json" >/dev/null
    echo "[runner] promote: staging -> prod pointer swap"
    # move prod to previous-good if set
    if [[ -s "${POINTERS_DIR}/current-prod" ]]; then
      cp -f "${POINTERS_DIR}/current-prod" "${POINTERS_DIR}/previous-good"
    fi
    printf '%s\n' "${bundle_dir%/}" > "${POINTERS_DIR}/current-prod"
    echo "[runner] OK: current-prod -> ${bundle_dir%/}"
    ;;

  rollback)
    ensure_pointers
    if [[ ! -s "${POINTERS_DIR}/previous-good" ]]; then
      echo "[runner] no previous-good pointer set" >&2
      exit 2
    fi
    echo "[runner] rollback: current-prod -> previous-good"
    cp -f "${POINTERS_DIR}/current-prod" "${POINTERS_DIR}/current-staging" 2>/dev/null || true
    cp -f "${POINTERS_DIR}/previous-good" "${POINTERS_DIR}/current-prod"
    echo "[runner] OK: current-prod rolled back"
    ;;

  status)
    ensure_pointers
    echo "[runner] pointers:"
    for f in current-staging current-prod previous-good; do
      printf "  %-14s %s\n" "$f:" "$(cat "${POINTERS_DIR}/${f}" 2>/dev/null || true)"
    done
    ;;

  stop)
    # v0 no-op; future: kill VM pidfiles
    echo "[runner] stop: v0 no-op (no VM yet)"
    ;;

  *)
    usage; exit 2;;
esac
