{ config, pkgs, lib, ... }:

let
  # Minimal "agent" smoke logic runs inside VM and writes to /mnt/artifacts
  smokeInner = pkgs.writeShellScript "example-agent-smoke" ''
    set -euo pipefail
    mkdir -p /mnt/artifacts

    # Prove we're in the guest
    echo "[guest] hello from example-agent VM" > /mnt/artifacts/guest-console.txt

    # Emit a run artifact from inside the VM (this becomes the authoritative run artifact)
    cat > /mnt/artifacts/run-artifact.json <<JSON
{
  "kind": "RunArtifact",
  "bundle": "example-agent@0.1.0",
  "lane": "staging",
  "backend": "qemu-local",
  "executedIn": "guest-vm",
  "startedAt": "$(date -Iseconds)",
  "endedAt": "$(date -Iseconds)",
  "result": "pass",
  "environment": {
    "kernel": "$(uname -r)",
    "arch": "$(uname -m)"
  }
}
JSON
  '';
in
{
  # Keep it tiny and deterministic
  boot.isContainer = false;
  networking.hostName = "example-agent";
  services.getty.autologinUser = "root";

  # 9p mount injected by host runner via QEMU_OPTS:
  # -virtfs local,path=<host_artifacts>,mount_tag=artifacts,security_model=none,id=artifacts
  fileSystems."/mnt/artifacts" = {
    device = "artifacts";
    fsType = "9p";
    options = [ "trans=virtio" "version=9p2000.L" "msize=104857600" "cache=mmap" ];
  };

  # One-shot unit runs smoke and powers off
  systemd.services.example-agent-smoke = {
    description = "Example Agent VM Smoke (writes artifacts then powers off)";
    wantedBy = [ "multi-user.target" ];
    after = [ "local-fs.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = smokeInner;
      ExecStartPost = "${pkgs.systemd}/bin/poweroff";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # Make sure basic tools exist
  environment.systemPackages = [ pkgs.coreutils pkgs.jq pkgs.systemd ];

  # NixOS requirement
  system.stateVersion = "24.11";
}
