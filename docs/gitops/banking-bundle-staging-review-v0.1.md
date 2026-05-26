# BankingBundleStagingReview v0.1

Issue refs: `SocioProphet/agentplane#239`, `SocioProphet/agentplane#168`

## Purpose

`BankingBundleStagingReview v0.1` is a metadata-only review record for the banking-twin execution bundle tranche discovered during branch-audit work.

It exists to preserve the bundle payload without silently admitting it as runnable AgentPlane runtime material.

The source branch is:

```text
banking-twin/agentplane-execution-bundles-v0-1
```

The first review record captures the four candidate bundles:

```text
stress-runner
capital-rollforward
filing-assembler
policy-audit
```

## Boundary

This record is not a bundle execution surface.

It does not add runnable bundles, execute smoke scripts, boot VM definitions, open network access, call providers, mutate workspace state, promote policy packs, admit runtime execution, or make production banking claims.

The record only captures the review posture needed before any later domain-specific or runtime-specific replay.

## Required bundle posture

Each bundle entry records:

```text
bundle_name
source_files
classification
target_repo_question
network_posture
artifact_write_posture
policy_pack_status
smoke_script_posture
vm_definition_posture
claim_posture
bundle_admission
review_findings
```

The first tranche treats all candidate bundles as staging material only.

## Policy interpretation

The validator enforces these first-capture rules:

- `nonProductionOnly` must be true.
- `review_scope` must be `metadata_only_no_execution`.
- The audited source branch must be recorded exactly.
- `bundle_count` must match the number of bundle entries.
- Each bundle must include `bundle.json`, `smoke.sh`, and `vm.nix` as repo-relative source-file references.
- DNS/HTTPS or NAT-style egress cannot be enabled for first capture.
- Writable artifact paths cannot be enabled for first capture.
- `UNSET` policy-pack placeholders require later pinning before runnable promotion.
- Smoke scripts must not be executable in first capture.
- VM definitions must not be bootable in first capture.
- Required non-goals must be present.

## Validation

```bash
python3 tools/validate_banking_bundle_staging_review.py tests/fixtures/reviews/banking-bundle-staging-review.valid.json
! python3 tools/validate_banking_bundle_staging_review.py tests/fixtures/reviews/banking-bundle-staging-review.network-enabled.invalid.json
```

## Next eligible tranche

After this metadata-only review lands, a later tranche may decide placement:

- keep as AgentPlane metadata fixtures only;
- replay into a banking-twin domain repo;
- move to a dedicated domain bundle repository;
- reject runnable promotion until policy-pack hashes and network posture are pinned.

That later tranche must remain separate from this first capture.
