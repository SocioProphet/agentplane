{ config, pkgs, lib, ... }:

let
  smokeInner = pkgs.writeShellScript "sourceos-image-production-smoke" ''
    set -euo pipefail
    echo "[guest] SourceOS image-production smoke start: $(date -Iseconds)" >&2

    if ! mountpoint -q /mnt/artifacts; then
      echo "[guest] ERROR: /mnt/artifacts is not a mountpoint" >&2
      mount >&2 || true
      exit 2
    fi

    cat > /mnt/artifacts/sourceos-image-production-run-artifact.json <<JSON
{
  "kind": "RunArtifact",
  "bundle": "sourceos-image-production-smoke@0.1.0",
  "lane": "staging",
  "backend": "qemu-local",
  "executedIn": "guest-vm",
  "startedAt": "$(date -Iseconds)",
  "endedAt": "$(date -Iseconds)",
  "result": "pass",
  "sourceosImageProduction": {
    "mode": "smoke",
    "artifactTruthRef": "SociOS-Linux/SourceOS:docs/ARTIFACT_TRUTH.md",
    "sociosAutomationRef": "SociOS-Linux/socios:pipelines/tekton/pipeline-customize-live-iso.yaml",
    "note": "This smoke module verifies bundle wiring only; it does not mutate host, invoke Tekton, or publish to Katello."
  },
  "environment": {
    "kernel": "$(uname -r)",
    "arch": "$(uname -m)"
  }
}
JSON

    echo "[guest] SourceOS image-production smoke done: $(date -Iseconds)" >&2
  '';
in
{
  services.getty.autologinUser = lib.mkForce null;
  systemd.services."getty@ttyAMA0".enable = lib.mkForce false;
  systemd.services."serial-getty@ttyAMA0".enable = lib.mkForce false;

  networking.hostName = "sourceos-image-production-smoke";

  boot.initrd.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];
  boot.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];

  fileSystems."/mnt/artifacts" = {
    device = "artifacts";
    fsType = "9p";
    options = [ "trans=virtio" "version=9p2000.L" "msize=104857600" "cache=mmap" ];
  };

  systemd.services.sourceos-image-production-smoke = {
    description = "SourceOS image-production VM Smoke (wiring proof only)";
    wantedBy = [ "basic.target" ];
    after = [ "local-fs.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = smokeInner;
      ExecStartPost = "${pkgs.bash}/bin/bash -lc '${pkgs.systemd}/bin/poweroff || true'";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  environment.systemPackages = [ pkgs.coreutils pkgs.util-linux pkgs.systemd ];
  system.stateVersion = "24.11";
}
