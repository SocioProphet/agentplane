{ lib, pkgs, ... }:
{
  system.stateVersion = "24.11";

  environment.systemPackages = with pkgs; [
    bash
    coreutils
    jq
  ];

  users.users.root.initialPassword = "banking-twin-dev-only";

  environment.etc."banking-twin/capital-rollforward.txt".text = ''
    bundle = capital-rollforward
    purpose = Capital and ratio roll-forward execution over projected banking state.
    status = staging-placeholder
  '';
}
