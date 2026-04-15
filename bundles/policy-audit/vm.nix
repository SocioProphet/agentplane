{ lib, pkgs, ... }:
{
  system.stateVersion = "24.11";

  environment.systemPackages = with pkgs; [
    bash
    coreutils
    jq
  ];

  users.users.root.initialPassword = "banking-twin-dev-only";

  environment.etc."banking-twin/policy-audit.txt".text = ''
    bundle = policy-audit
    purpose = Policy and control-matrix audit bundle for banking twin runs.
    status = staging-placeholder
  '';
}
