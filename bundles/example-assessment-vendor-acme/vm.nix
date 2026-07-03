{ config, pkgs, lib, ... }:

let
  smokeInner = pkgs.writeShellScript "example-assessment-vendor-acme-smoke" ''
    set -euo pipefail
    echo "[guest] assessment smoke start: $(date -Iseconds)" >&2

    if ! mountpoint -q /mnt/artifacts; then
      echo "[guest] ERROR: /mnt/artifacts is not a mountpoint" >&2
      mount >&2 || true
      exit 2
    fi

    touch /mnt/artifacts/.writetest || { echo "[guest] ERROR: /mnt/artifacts not writable" >&2; exit 2; }
    rm -f /mnt/artifacts/.writetest

    cat > /mnt/artifacts/run-artifact.json <<JSON
{
  "kind": "RunArtifact",
  "bundle": "example-assessment-vendor-acme@0.1.0",
  "lane": "staging",
  "backend": "qemu-local",
  "executedIn": "guest-vm",
  "result": "pass",
  "subjectId": "vendor:acme-cloud",
  "frameworkId": "nist-800-53-rev5"
}
JSON

    cat > /mnt/artifacts/assessment-receipt.json <<JSON
{
  "receipt_id": "receipt_vendor_acme_assessment_001",
  "trace_id": "trace_vendor_acme_assessment_001",
  "evaluation_refs": ["eval_nist_ac_2_001"],
  "finding_refs": ["finding_nist_ac_2_001"],
  "replay": { "manifest_ref": "replay://vendor-acme-assessment/001", "replayable": true },
  "sealed_at": "$(date -Iseconds)"
}
JSON

    echo "[guest] assessment smoke done: $(date -Iseconds)" >&2
  '';
in
{
  services.getty.autologinUser = lib.mkForce null;
  systemd.services."getty@ttyAMA0".enable = lib.mkForce false;
  systemd.services."serial-getty@ttyAMA0".enable = lib.mkForce false;

  networking.hostName = "example-assessment-vendor-acme";

  boot.initrd.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];
  boot.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];

  fileSystems."/mnt/artifacts" = {
    device = "artifacts";
    fsType = "9p";
    options = [ "trans=virtio" "version=9p2000.L" "msize=104857600" "cache=mmap" ];
  };

  systemd.services.example-assessment-vendor-acme-smoke = {
    description = "Example Assessment Vendor Acme VM Smoke";
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
