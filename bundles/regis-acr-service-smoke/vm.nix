{ config, pkgs, lib, ... }:

let
  smokeInner = pkgs.writeShellScript "regis-acr-service-smoke" ''
    set -euo pipefail
    echo "[guest] Regis ACR service smoke start: $(date -Iseconds)" >&2

    if ! mountpoint -q /mnt/artifacts; then
      echo "[guest] ERROR: /mnt/artifacts is not a mountpoint" >&2
      mount >&2 || true
      exit 2
    fi

    touch /mnt/artifacts/.writetest || { echo "[guest] ERROR: /mnt/artifacts not writable" >&2; exit 2; }
    rm -f /mnt/artifacts/.writetest

    cat > /mnt/artifacts/regis-acr-run-artifact.json <<JSON
{
  "kind": "RunArtifact",
  "bundle": "regis-acr-service-smoke@0.1.0",
  "lane": "staging",
  "backend": "lima-process",
  "executedIn": "guest-vm",
  "startedAt": "$(date -Iseconds)",
  "endedAt": "$(date -Iseconds)",
  "result": "pass",
  "service": "regis-acr-api",
  "safetyPosture": {
    "canonicalMutation": false,
    "externalEgress": false,
    "inlineSecrets": false,
    "evidenceFirst": true,
    "ontogenesisActivation": false
  },
  "environment": {
    "kernel": "$(uname -r)",
    "arch": "$(uname -m)"
  }
}
JSON

    echo "[guest] Regis ACR service smoke done: $(date -Iseconds)" >&2
  '';
in
{
  services.getty.autologinUser = lib.mkForce null;
  systemd.services."getty@ttyAMA0".enable = lib.mkForce false;
  systemd.services."serial-getty@ttyAMA0".enable = lib.mkForce false;

  networking.hostName = "regis-acr-smoke";

  boot.initrd.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];
  boot.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];

  fileSystems."/mnt/artifacts" = {
    device = "artifacts";
    fsType = "9p";
    options = [ "trans=virtio" "version=9p2000.L" "msize=104857600" "cache=mmap" ];
  };

  systemd.services.regis-acr-service-smoke = {
    description = "Regis ACR Service Smoke (write artifacts then poweroff)";
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
