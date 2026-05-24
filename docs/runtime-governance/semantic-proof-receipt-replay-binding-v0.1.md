# Semantic-proof receipt and replay binding v0.1

## Purpose
This note defines the first runtime-facing binding between imported semantic-proof assets and the existing `agentplane` receipt / replay surfaces.

## Inputs
- imported manifest under `policy/imports/semantic-proof/`
- proof references emitted from the standards-side semantic-proof canon
- transport-facing carriage from `TriTRPC`

## Runtime binding rules
1. Receipt assembly may include `proof_refs` and `verification_results` in the evidence block.
2. Replay materialization may include `proof_ids_attached` and a replay boundary hash in the replay block.
3. Transport failures remain transport failures and must not be rewritten as proof verifier failures.
4. Imported proof bundles remain externally versioned and are not redefined locally in `agentplane`.

## Minimal hook points
- receipt builder / evidence assembly path
- replay artifact materialization path
- imported-bundle version pinning under `policy/imports/semantic-proof/`

## Follow-on
- bind the imported manifest to a receipt smoke test
- bind verifier outcomes to a replay artifact example
- add explicit failure examples where transport and proof failures are both present but kept distinct
