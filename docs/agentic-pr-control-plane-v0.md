# Agentic PR Control Plane v0

Date: 2026-05-03  
Status: Proposed  
Owning repo: `SocioProphet/agentplane`  
Paired policy issue: `SocioProphet/policy-fabric#44`  
Tracking issue: `SocioProphet/agentplane#82`

## Purpose

AgentPlane should treat agentic software development as evidence-producing execution, not as an unbounded chat session. The v0 Agentic PR Control Plane defines the repo-native lifecycle for turning a scoped GitHub issue into a bounded draft pull request, adversarial review, policy-gated merge decision, and durable ledger record.

The design target is not a Copilot-style chat surface. The target is the development operating system around agent work: issue intake, repo snapshotting, sandboxed execution, patch production, diff hygiene, CI evidence, review decisions, merge gates, and post-merge auditability.

## Core lifecycle

```text
Issue
  -> Task Planner
  -> Repo Snapshot
  -> Sandbox Runner
  -> Patch Producer
  -> Diff Hygiene Gate
  -> CI Runner
  -> Review Agent
  -> PR Publisher
  -> Merge Gate
  -> Post-merge Ledger
```

Each stage emits or consumes explicit evidence. Hidden model memory is never sufficient evidence for scope, safety, review, or merge authority.

## Non-negotiable authority split

No single actor receives implementation, review, and merge authority.

```text
Implementation agent may propose.
Review agent may approve, comment, or request changes.
Policy gate may merge or block.
```

This keeps a useful implementation agent from becoming an unbounded autonomous committer. It also prevents a review agent from laundering an unsafe diff into the default branch when the policy gate has not accepted the branch state, CI evidence, head SHA, and hygiene posture.

## Service boundaries

### `taskd`

`taskd` converts a GitHub issue into a typed work order. The issue is the executable specification, not just a human ticket.

The work order must include:

- repository and issue references;
- objective;
- expected files or allowed path set;
- maximum changed-file count and allowance;
- explicit non-goals;
- allowed side effects;
- validation commands;
- review checklist;
- required PR body sections;
- policy references;
- ledger fields.

### `repod`

`repod` establishes the repository truth snapshot before any implementation action. It records default branch, base commit, branch divergence, relevant repo-local guidance, current open PR state where available, and file/path boundaries from the work order.

`repod` should not infer broad repo strategy. It exposes safe file operations against the bounded task contract.

### `sandboxd`

`sandboxd` executes implementation work in a disposable workspace. The workspace must be easy to destroy and must not leak virtual environments, dependency caches, local credentials, editor state, or generated dependency trees into the final patch.

The sandbox is allowed to install tools for execution. The patch is not allowed to vendor the sandbox.

### `patchd`

`patchd` creates the branch, commits bounded file changes, and opens a draft pull request. It refuses generated dependency trees unless the issue contract explicitly permits them.

A `patchd` output must include:

- changed-file summary;
- validation commands attempted;
- validation outcome;
- known gaps;
- self-critique;
- linked issue;
- policy evidence or gate posture.

### `reviewd`

`reviewd` performs adversarial review after the diff hygiene gate has passed. It checks scope, claims, test evidence, docs precision, schema correctness, compatibility with repo conventions, and whether the implementation exceeded the issue contract.

`reviewd` has only three outcomes:

- approve;
- request changes;
- comment.

It does not merge.

### `gated`

`gated` owns merge authority. It verifies branch freshness, expected head SHA, CI/check status, required review state, diff hygiene posture, and issue-authorized exceptions.

A reviewer approval is not sufficient if `gated` sees a stale branch, unknown head SHA, denied path, binary blob, virtual environment, generated dependency tree, or missing validation evidence.

### `ledgerd`

`ledgerd` records what happened and why. At minimum, the ledger record should include:

- issue reference;
- repository;
- branch;
- base SHA;
- head SHA;
- implementation actor;
- review actor;
- merge actor or gate;
- changed files;
- validation commands and outcomes;
- hygiene verdict;
- review verdict;
- merge verdict;
- exception rationale, if any.

## Diff hygiene before semantic review

Diff hygiene must run before semantic review. A PR that commits `.venv-tools/`, `node_modules/`, package caches, binary blobs, local secrets, unrelated rewrites, or hundreds of unexpected files should be blocked before a reviewer agent spends time on correctness.

The paired Policy Fabric issue, `SocioProphet/policy-fabric#44`, owns the enforceable Diff Hygiene Gate v0. AgentPlane owns the execution lifecycle and must present enough work-order and PR evidence for Policy Fabric to decide.

## Repo-local memory contract

The agent may use model memory, but the enforceable contract must be repo-local and policy-readable. Before writing, an implementation agent should read available repo guidance such as:

- `README.md`;
- `CONTRIBUTING.md`;
- `AGENTS.md`, if present;
- schema indexes;
- relevant docs and ADRs;
- linked issue body;
- paired policy issue;
- recent branch and PR state.

Hidden memory may inform implementation. It does not authorize scope expansion.

## Integration map

| Repository | Responsibility |
|---|---|
| `SocioProphet/agentplane` | Agent lifecycle, work-order contract, sandbox execution evidence, draft PR production, run/replay/ledger evidence shape. |
| `SocioProphet/policy-fabric` | Diff hygiene rules, merge gate semantics, deny paths, exception policy, branch freshness requirements, policy verdicts. |
| `SocioProphet/prophet-platform` | Product-surface work, release artifacts, demo/readiness evidence, downstream platform integration. |
| `SocioProphet/global-devsecops-intelligence` | Security intelligence, anti-pattern detection, suspicious diff classification, incident learning loops. |
| `SocioProphet/ontogenesis` | Typed ontology for task, actor, authority, workflow, evidence, and governance relationships. |
| `SocioProphet/sociosphere` | Workspace orchestration, operator UX, issue/PR/review dashboarding, human steering surface. |

## Minimal v0 success criteria

The first useful system does not need a large service mesh. It needs a strict contract and one narrow executable lane:

1. An issue produces an `AgenticPRWorkOrder`.
2. The implementation agent opens a draft PR only.
3. The diff hygiene gate evaluates changed files before review.
4. The review agent produces approve/request-changes/comment only.
5. The merge gate validates head SHA, CI, review, and hygiene posture.
6. The ledger records what happened.

## Explicit non-goals for v0

- No production service deployment.
- No autonomous self-merge.
- No hidden approval based on model confidence.
- No dependency vendoring unless the issue contract explicitly allows it.
- No repo-wide formatting or unrelated product-surface rewrites.
- No production-readiness claim without validation evidence and policy acceptance.

## Open design backlog

- Define a durable `AgenticPRRunArtifact` if the generic `RunArtifact` is not precise enough.
- Add a Policy Fabric verdict import shape for diff hygiene outcomes.
- Add a GitHub Actions workflow that fails on denied generated paths.
- Add a reviewer-agent prompt contract once the policy contract is stable.
- Decide whether merge-gate evidence should be a first-class AgentPlane artifact or imported from Policy Fabric.
