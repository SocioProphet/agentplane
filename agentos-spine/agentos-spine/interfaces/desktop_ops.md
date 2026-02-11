# DesktopOpsAPI (v0.1)

Goal: OS/GUI automation when browser-only is insufficient.

## Safety requirements (hard)

- runs in a sandbox (VM / container + display proxy)
- no ambient secrets
- explicit allowlist of filesystem mounts
- explicit network egress rules

## Provider

- Agent-S
