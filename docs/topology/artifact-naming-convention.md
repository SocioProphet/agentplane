# Artifact naming convention

This note proposes a simple naming convention for control-plane evidence references.

## Goal

Promotion and rollback references should be inspectable and comparable across repos without inventing ad hoc names every time.

## Suggested pattern

```text
<lane>:<artifact-kind>:<subject>:<version-or-sha>
```

Examples:

- `sourceos:image:builder-aarch64:sha256-abc123`
- `sourceos:eval:builder-aarch64:2026-04-15T19-00Z`
- `sourceos:policy:baseline:policy-0001`
- `sourceos:rollback:stable:sha256-def456`

## Promotion references

A promotion record should prefer explicit references for:

- artifact set
- evaluation bundle
- policy snapshot
- benchmark snapshot
- rollback target

## Relationship to standards

This repository uses shared channel and capability terms from `SocioProphet/socioprophet-agent-standards`.

This note only proposes a naming convention for evidence references carried by the control-plane lifecycle.
