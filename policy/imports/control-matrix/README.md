# Control matrix import lane

This directory holds imported Agentic Control Matrix bundles for `agentplane`.

## Source of truth

The canonical standards package lives in:

- `SocioProphet/socioprophet-standards-storage`

`agentplane` is the consumer/runtime lane. It should import and pin released bundle versions from the standards repository rather than redefining the ontology locally.

## Seed state

This PR adds the import manifest and expected bundle paths so the runtime lane has a stable place to bind:

- policy bundle
- monitor bundle
- test bundle

## Next step

After the standards PR merges, pin the released package version and bind the imported policy bundle to the first runtime enforcement surface.
