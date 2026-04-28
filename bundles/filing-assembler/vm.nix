{ lib, pkgs, ... }:
{
  system.stateVersion = "24.11";

  environment.systemPackages = with pkgs; [
    bash
    coreutils
    jq
  ];

  users.users.root.initialPassword = "banking-twin-dev-only";

  environment.etc."banking-twin/filing-assembler.txt".text = ''
    bundle = filing-assembler
    purpose = Evidence-bound filing-pack assembly for regulatory and management outputs.
    status = staging-placeholder
  '';
}
