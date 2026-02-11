# Rollout plan (first 90 days)

## Phase 0: Hygiene + license truth (blocking)

- Ensure every spine repo has an explicit LICENSE file
- Remove accidental junk from snapshots: .DS_Store, .venv, __pycache__, *.pyc, nested .git
- Add CI gates so junk cannot re-enter

## Phase 1: Conformance gates

- TriTRPC fixtures + determinism tests are executable and green
- Standards repos validate schema IDs and enforce formatting

## Phase 2: Workspace materialization

- Use sociosphere runner (or equivalent) to materialize pinned repos
- One command runs: fetch -> validate -> verify fixtures

## Phase 3: OS integration substrate (local)

- Base packages, sandbox runner, secrets broker
- Install core tools (executors, orchestrator) behind agentctl

## Phase 4: Providers boxed + replacement projects

- AD4M behind MeaningGraphAPI + contract tests
- Fortemi behind KnowledgeBaseAPI + start KB-Core replacement
- Inbox Zero behind MailOpsAPI + start MailOps-Core replacement (optional)
