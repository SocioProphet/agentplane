# Banking Execution Bundles Audit — 2026-05-25

Issue: `SocioProphet/agentplane#168`

Source branch audited:

```text
banking-twin/agentplane-execution-bundles-v0-1
```

## Finding

The branch contains a banking-domain execution-bundle tranche:

```text
bundles/stress-runner/bundle.json
bundles/stress-runner/smoke.sh
bundles/stress-runner/vm.nix
bundles/capital-rollforward/bundle.json
bundles/capital-rollforward/smoke.sh
bundles/capital-rollforward/vm.nix
bundles/filing-assembler/bundle.json
bundles/filing-assembler/smoke.sh
bundles/filing-assembler/vm.nix
bundles/policy-audit/bundle.json
bundles/policy-audit/smoke.sh
bundles/policy-audit/vm.nix
docs/banking-execution-bundles.md
```

The branch documentation states that these are staging bundles, not final production bundles. Their stated purpose is to establish bundle names, bind banking execution lanes to policy-pack references, and make replay/evidence expectations visible before runtime services are implemented.

## Risk classification

This branch is **not safe for blind replay**.

Reasons:

- It is domain-specific to the banking-twin initiative.
- It adds execution bundles, smoke scripts, and Nix VM definitions.
- The representative bundle uses writable artifact mounts and NAT networking with DNS/HTTPS egress allowance.
- The representative smoke script creates files under `/mnt/artifacts`.
- Policy pack hashes are unset in the staging bundle examples.
- Domain claims and expected upstream references need review before the bundles are treated as canonical AgentPlane fixtures.

## Disposition

Hold for domain and runtime-boundary review.

Do not replay this branch until a separate issue defines:

- whether these bundles belong in generic `agentplane` or a banking-specific repo;
- exact claim posture for banking-twin staging bundles;
- allowed network posture;
- whether smoke scripts may write under `/mnt/artifacts` in CI fixtures;
- whether policy pack hashes must be pinned before merge;
- whether the bundle docs need non-production-only disclaimers;
- whether a synthetic, non-executing validation workflow is enough for first capture.

## Safe next step

Open a dedicated review issue for banking execution bundles rather than merging the branch.

Suggested title:

```text
Review banking-twin execution bundle staging tranche
```

Suggested acceptance criteria:

- classify each bundle as generic AgentPlane fixture, banking-twin domain fixture, or out-of-scope;
- require `nonProductionOnly: true` or equivalent staging posture;
- require pinned policy-pack refs or explicit `UNSET` fixture allowance;
- syntax-check JSON, shell, and Nix files without executing smoke scripts;
- record network posture and artifact-write posture explicitly;
- decide target repo placement.

## Boundary

This audit does not replay the branch payload.

It does not add bundles, smoke scripts, Nix VM definitions, banking domain claims, runtime execution, provider calls, network activity, or workspace mutation.
