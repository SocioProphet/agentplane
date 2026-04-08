# State Pointer Model

agentplane maintains three plain-text pointer files under `state/pointers/` to track which
bundle is currently active at each lane and what the last known-good prod bundle was.

---

## Pointer files

| File | Contents | Written by |
|---|---|---|
| `current-staging` | Path to the currently active staging bundle directory | `runners/qemu-local.sh run --profile staging` |
| `current-prod` | Path to the currently active production bundle directory | `runners/qemu-local.sh promote` |
| `previous-good` | Copy of `current-prod` before the most recent promotion | `runners/qemu-local.sh promote` |

Each file contains a single line: the relative path to a bundle directory (e.g.,
`bundles/example-agent`).

The files are created empty by `ensure_pointers()` inside `runners/qemu-local.sh` if they do
not yet exist. `state/pointers/.keep` ensures the directory exists in the repository even though
the pointer files themselves are gitignored at runtime (see `.gitignore`).

---

## Lifecycle

### On `run`

```
runners/qemu-local.sh run <bundle-dir> --profile staging
```

1. Validates the bundle.
2. Selects an executor.
3. Executes the bundle (lima-process or QEMU path).
4. Emits artifacts.
5. Writes `bundle-dir` to `state/pointers/current-staging`.

### On `promote`

```
runners/qemu-local.sh promote <bundle-dir>
```

1. Validates the bundle.
2. Copies `current-prod` → `previous-good` (if `current-prod` is non-empty).
3. Writes `bundle-dir` to `state/pointers/current-prod`.

### On `rollback`

```
runners/qemu-local.sh rollback
```

1. Fails if `previous-good` is empty (nothing to roll back to).
2. Copies `current-prod` → `current-staging`.
3. Copies `previous-good` → `current-prod`.

### On `status`

```
runners/qemu-local.sh status
```

Prints the current value of all three pointer files.

---

## Gitignore behaviour

The pointer files are **gitignored** (`state/pointers/*` with `!state/pointers/.keep` in
`.gitignore`). This is intentional: pointer state is machine-local and must not be committed.

Only `state/pointers/.keep` is tracked in git to ensure the directory exists in fresh clones.

---

## Future evolution

In a multi-node fleet deployment, the pointer model will shift from plain text files on the
control-plane host to a distributed state store (e.g., a key-value service or a git-backed
state repo). The runner interface (`status`, `promote`, `rollback`) will remain unchanged;
the backend that reads and writes pointers will be abstracted.
