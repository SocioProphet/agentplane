{ config, pkgs, lib, ... }:

let
  smokeInner = pkgs.writeShellScript "professional-intelligence-smoke" ''
    set -euo pipefail
    echo "[guest] Professional Intelligence smoke start: $(date -Iseconds)" >&2

    if ! mountpoint -q /mnt/artifacts; then
      echo "[guest] ERROR: /mnt/artifacts is not a mountpoint" >&2
      mount >&2 || true
      exit 2
    fi

    touch /mnt/artifacts/.writetest || { echo "[guest] ERROR: /mnt/artifacts not writable" >&2; exit 2; }
    rm -f /mnt/artifacts/.writetest

    cat > /mnt/artifacts/professional-intelligence-workflow-step.json <<JSON
{
  "kind": "ProfessionalIntelligenceWorkflowStep",
  "schemaVersion": "v0.1",
  "workflowId": "client-opportunity-review",
  "stepId": "review-packet",
  "capability": "agent-fabric",
  "workroomRef": "workroom://workroom-demo-0001",
  "contextRefs": ["context-pack://pi-demo-0001", "entity://organization/org-demo-0001"],
  "policyDecisionRefs": ["policy-decision://ppd-review-0001"],
  "obligationRefs": ["obligation://obl-ai-use-demo-0001"],
  "result": "requires_review",
  "startedAt": "$(date -Iseconds)",
  "endedAt": "$(date -Iseconds)"
}
JSON

    cat > /mnt/artifacts/run-artifact.json <<JSON
{
  "kind": "RunArtifact",
  "bundle": "professional-intelligence-client-opportunity-review@0.1.0",
  "lane": "staging",
  "backend": "qemu-local",
  "executedIn": "guest-vm",
  "startedAt": "$(date -Iseconds)",
  "endedAt": "$(date -Iseconds)",
  "result": "pass",
  "evidenceRefs": ["professional-intelligence-workflow-step.json"]
}
JSON

    cat > /mnt/artifacts/replay-artifact.json <<JSON
{
  "kind": "ReplayArtifact",
  "bundle": "professional-intelligence-client-opportunity-review@0.1.0",
  "inputs": ["bundle.json", "vm.nix", "smoke.sh"],
  "expectedOutputs": ["professional-intelligence-workflow-step.json", "run-artifact.json"],
  "createdAt": "$(date -Iseconds)"
}
JSON

    echo "[guest] Professional Intelligence smoke done: $(date -Iseconds)" >&2
  '';
in
{
  services.getty.autologinUser = lib.mkForce null;
  systemd.services."getty@ttyAMA0".enable = lib.mkForce false;
  systemd.services."serial-getty@ttyAMA0".enable = lib.mkForce false;

  networking.hostName = "pi-workflow";

  boot.initrd.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];
  boot.kernelModules = [ "virtio_pci" "virtio_ring" "9p" "9pnet" "9pnet_virtio" ];

  fileSystems."/mnt/artifacts" = {
    device = "artifacts";
    fsType = "9p";
    options = [ "trans=virtio" "version=9p2000.L" "msize=104857600" "cache=mmap" ];
  };

  systemd.services.professional-intelligence-smoke = {
    description = "Professional Intelligence VM smoke evidence emitter";
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
