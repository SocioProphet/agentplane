{ lib, pkgs, ... }:
{
  system.stateVersion = "24.11";

  environment.systemPackages = with pkgs; [
    bash
    coreutils
    jq
  ];

  users.users.root.initialPassword = "banking-twin-dev-only";

  environment.etc."banking-twin/stress-runner.txt".text = ''
    bundle = stress-runner
    purpose = Scenario-conditioned stress execution over a GAIA banking twin snapshot.
    status = staging-placeholder
  '';
}
