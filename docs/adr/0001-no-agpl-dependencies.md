# ADR-0001: No AGPL dependencies

Date: 2026-02-10  
Status: Accepted

## Context

agentplane is MIT-licensed and is designed to be used as a foundation for enterprise products
and third-party integrations. The GNU Affero General Public License (AGPL) requires that network
users be given access to the source code of the entire combined work. Including any AGPL-licensed
dependency in agentplane — even transitively — would impose copyleft conditions on all downstream
consumers and could disqualify it from enterprise environments that prohibit AGPL software.

## Decision

No AGPL-licensed dependency may appear in this repository — in production code, in tooling,
or in bundle contents. This constraint is:

1. Encoded in the bundle schema: `metadata.licensePolicy.allowAGPL` must be `false`
   ([schemas/bundle.schema.v0.1.json](../../schemas/bundle.schema.v0.1.json), line 24–28).
2. Enforced at validation time: `scripts/validate_bundle.py` hard-fails if
   `allowAGPL` is not explicitly `false`.
3. Applied to repository tooling: no AGPL tools may be added as development dependencies.

## Consequences

- **Positive:** Downstream users and enterprise integrators can adopt agentplane without
  copyleft concerns.
- **Positive:** The constraint is machine-enforced, not just a policy statement.
- **Negative:** Some otherwise useful libraries (e.g., certain graph-processing or data-science
  tools released under AGPL) cannot be used. Alternatives under MIT, Apache 2.0, BSD, or MPL
  must be chosen instead.
- **Negative:** Contributors must check the license of any new dependency before adding it.
  The CI pipeline does not yet run an automated license scanner; this is a manual obligation.
