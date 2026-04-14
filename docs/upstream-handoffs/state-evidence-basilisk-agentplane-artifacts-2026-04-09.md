# State / Projection / Evidence kernel artifact manifest

Date: 2026-04-09
Related PR: #23
Target upstream repos:
- `basilisk-labs/agentplane`
- `basilisk-labs/agentplane-recipes`

## Verified upstream heads used for this ladder

### `basilisk-labs/agentplane`
- `main`
- `1bb989422caa8c476fed0c8c693b1191bee1d655`
- `workflow: reconcile stale shipped task state (#164)`

### `basilisk-labs/agentplane-recipes`
- `main`
- `021c99bc8527220bf9339872903cf30105adea97`
- `Remove legacy requires_human_approval from Dokploy recipe`

## Artifact inventory (sandbox-generated)

### Primary execution bundle
- `state-evidence-pr-bundle.v8.zip`
- sha256: `c166b92d86fabddfaf07535f575d0072a3260fddc14b872e1b87590a609fff0b`

### Apply script
- `apply_state_evidence_patches.v8.sh`
- sha256: `26d4215d07e2ac4375415f76f5d500b46a6616c9e91d9b74d96faf412618e7e3`

### AgentPlane patch ladder
1. `agentplane-state-evidence-incidents.v2.patch`
   - sha256: `323adfe5e133e14550b261d4e7d25fb0d2a81a483274a900edf9b152c7b16b0b`
2. `agentplane-incidents-evidence-pack.tests.pr2.patch`
   - sha256: `504dbccec0e293f60c52f132228773850e73297313ef486164fbd70dff7f973c`
3. `agentplane-task-explain.pr1.patch`
   - sha256: `61b7da0a56ee50f02542cbc96411638fa121ad8c8fea3d65c20113d86e169eeb`
4. `agentplane-task-reconcile-and-ci.pr1.patch`
   - sha256: `56b8a6cc078a286a0691f7c6fd5c3c48a45400ccbc27b23a39765d7735044d59`
5. `agentplane-task-explain-evidence-expansion.pr2.patch`
   - sha256: `65623ae7cbc75262d992a583d8e209589de45ae1dcfa32bc2781898a0179e199`
6. `agentplane-backend-snapshot-sync-conflicts.pr4.patch`
   - sha256: `07ce6d4a730ac25ab9feee636c1e94bb48b0263b161aa2eef5221d7186b5fdf9`
7. `agentplane-backend-warning-metadata.pr5.patch`
   - sha256: `c87955e3c8057d5acdcc22e1b3a589de5291829169265a759fcd7025e020ca79`

### AgentPlane Recipes patch ladder
1. `agentplane-recipes-state-drift-lab.pr1.patch`
   - sha256: `ed88e36fe94e07d7c787f534b604d2e7399093f0b569d8e1f8f55f808587cba8`
2. `agentplane-recipes-state-drift-lab-integrity.pr2.patch`
   - sha256: `bda943a818b75c12f65b5b8073dcc0c3f0036216028314202a7dcbda4b0b38ad`

### Recipe release artifact
- `state-drift-lab-0.1.0.tar.gz`
- sha256: `007acf9610313ac7e9d44ef3b34957c5634417169dd94466c786e95e4f75de4b`

### Catalog entry snippet
- `index-entry.state-drift-lab.v0.1.1.json`
- sha256: `be3203d423f1385a2518a1f6caab8b3632a9ad897e5a6107e6aeef92a7e1adb7`

## Intended apply order

```bash
./apply_state_evidence_patches.v8.sh /path/to/agentplane /path/to/agentplane-recipes --with-tests
```

Equivalent explicit order:

1. `agentplane-state-evidence-incidents.v2.patch`
2. `agentplane-incidents-evidence-pack.tests.pr2.patch`
3. `agentplane-task-explain.pr1.patch`
4. `agentplane-task-reconcile-and-ci.pr1.patch`
5. `agentplane-task-explain-evidence-expansion.pr2.patch`
6. `agentplane-backend-snapshot-sync-conflicts.pr4.patch`
7. `agentplane-backend-warning-metadata.pr5.patch`
8. `agentplane-recipes-state-drift-lab.pr1.patch`
9. `agentplane-recipes-state-drift-lab-integrity.pr2.patch`

## Minimum live test lane after apply

```bash
bun x vitest run \
  packages/agentplane/src/runtime/incidents/resolve.test.ts \
  packages/agentplane/src/commands/task/explain.unit.test.ts \
  packages/agentplane/src/commands/task/reconcile.unit.test.ts
```

## Minimum smoke checks after apply

```bash
bun run agentplane incidents collect <task-id> --evidence-pack --json
bun run agentplane task explain <task-id>
bun run agentplane task reconcile <task-id>
```

## Reason this is recorded here

The target upstream repositories are outside the current connector's write scope. This manifest preserves the exact patch inventory and verification hashes in a write-capable GitHub repo until write scope for `basilisk-labs/*` is enabled.
