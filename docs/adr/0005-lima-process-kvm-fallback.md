# ADR-0005: lima-process fallback when KVM is absent

Date: 2026-02-10  
Status: Accepted

## Context

The primary execution backend for agentplane is QEMU (via `nix build` + a NixOS VM). However,
the default local executor (`lima-nixbuilder`) runs on a macOS host with a Lima VM that uses
TCG (software emulation) rather than KVM hardware acceleration. Running a nested QEMU VM inside
TCG is extremely slow and prone to hangs.

Two options were evaluated:

1. **Fail fast** — Detect `kvm: false` and refuse to run `qemu`/`microvm` backends, requiring
   the operator to provision a KVM-capable host.
2. **Transparent fallback** — Automatically switch to `lima-process` when the executor
   reports `kvm: false`.

## Decision

When `spec.vm.backendIntent` is `qemu` or `microvm` and the selected executor has `caps.kvm:
false`, the runner transparently falls back to `lima-process`. The bundle's agent run is
executed directly inside the Lima VM (not inside a nested QEMU VM), and the full evidence chain
is still produced.

This is implemented in `runners/qemu-local.sh` (the KVM cap guard block) and documented in
[docs/executors.md](../executors.md).

The executor selection precedence (bundle pin → fleet inventory default → `/etc/nix/machines`
fallback) is also documented in [docs/executors.md](../executors.md).

## Consequences

- **Positive:** Local development works on macOS + Lima without requiring a bare-metal KVM host.
- **Positive:** The full evidence chain is still produced in the fallback path.
- **Negative:** The fallback is silent by default (it logs a line but does not warn that the
  original backend intent was overridden). Operators who require true VM isolation must ensure
  their executor has `kvm: true`.
- **Negative:** `lima-process` does not provide the same isolation guarantees as a full QEMU VM.
  For production runs requiring strong isolation, a KVM-capable executor is required.
