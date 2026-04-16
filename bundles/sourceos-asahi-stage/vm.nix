{ lib, pkgs, ... }:
{
  system.stateVersion = "25.05";

  users.users.root.initialPassword = "sourceos-stage";

  services.getty.autologinUser = lib.mkForce "root";

  environment.systemPackages = with pkgs; [
    bash
    coreutils
    jq
    findutils
    gnugrep
  ];

  systemd.services.sourceos-stage-smoke = {
    description = "SourceOS Asahi stage smoke validation";
    wantedBy = [ "multi-user.target" ];
    after = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "/bin/sh /etc/sourceos/smoke.sh";
      RemainAfterExit = true;
    };
  };

  environment.etc."sourceos/smoke.sh".text = ''
    #!${pkgs.bash}/bin/bash
    set -euo pipefail
    test -d /mnt/config
    test -d /mnt/evidence
    if [ -e /var/run/sourceos-secrets/HN_TICK_API_KEY_FILE ]; then
      test -s /var/run/sourceos-secrets/HN_TICK_API_KEY_FILE
    fi
    echo '{"stage":"ok","bundle":"sourceos-asahi-stage"}' > /mnt/evidence/stage-health.json
  '';
}
