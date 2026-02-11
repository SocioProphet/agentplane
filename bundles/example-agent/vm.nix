{ config, pkgs, lib, ... }:

let
  smokeInner = pkgs.writeShellScript "example-agent-smoke" ''
    set -euo pipefail

    # Hard requirement: artifacts mount must exist and be writable
    if ! mountpoint -q /mnt/artifacts; then
      echo "[guest] ERROR: /mnt/artifacts is not a mountpoint" >&2
      mount >&2 || true
      exit 2
    fi
    touch /mnt/artifacts/.writetest || { echo "[guest] ERROR: /mnt/artifacts not writable" >&2; exit 2; }
    rm -f /mnt/artifacts/.writetest

    echo "[guest] hello from example-agent VM" > /mnt/artifacts/guest-console.txt
    echo "[guest] proof: $(date -Iseconds)" > /mnt/artifacts/guest-proof.txt

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
  boot.isContainer = false;
  networking.hostName = "example-agent";
  services.getty.autologinUser = "root";

  fileSystems."/mnt/artifacts" = {
    device = "artifacts";
    fsType = "9p";
    options = [ "trans=virtio" "version=9p2000.L" "msize=104857600" "cache=mmap" ];
  };

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

  environment.systemPackages = [ pkgs.coreutils pkgs.util-linux pkgs.systemd ];
  system.stateVersion = "24.11";
}
