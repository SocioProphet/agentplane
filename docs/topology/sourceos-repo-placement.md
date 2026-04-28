# SourceOS repository placement

## Decision

`agentplane` is the canonical home for the SourceOS execution and promotion control plane.

It owns:

- bundle lifecycle
- executor placement
- run and replay evidence
- promotion and reversal semantics
- fleet and channel topology
- operator-facing control-plane documentation

## Cross-repo split

### SocioProphet/agentplane
Owns the control-plane contract and topology.

### SocioProphet/socioprophet-agent-standards
Owns the normative schema, policy, conformance, and compatibility canon.

### SociOS-Linux/source-os
Owns Linux host, image, and Nix realization.

### SociOS-Linux/socios-scripts
Owns installer and migration helper scripts.

### SociOS-Linux/socios-alarm-builder
Owns x86/ALARM reference image assembly.

## Rule

Until a dedicated live ops repository exists, `agentplane` defines the control-plane model, `socioprophet-agent-standards` defines the normative contract, and `source-os` realizes the Linux build and host surfaces.

Packaging or adaptor repositories such as `nix-openclaw` are downstream integration surfaces and are not the canonical control-plane home.
