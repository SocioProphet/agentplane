# SEM-K Semantic Control

SEM-K is the bridge between visible symbolic layers and AgentPlane runtime governance.

## Control boundary

SCT-K and STN-K are visible, inspectable symbolic layers. They may signal lineage and intent, but they do not authorize runtime behavior. Runtime authority comes only from a signed, audience-bound, non-expired SCTControlProfile sidecar that passes validation and projection checks.

Core rule:

> Public signal may carry meaning. Only signed sidecar authorization may govern execution.

## Chain

```text
SCT-K -> STN-K -> SEM-K -> SCTControlProfile -> AgentPlane -> Evidence / Replay
```

## Narrow seam

SocioSphere may emit upstream workspace artifacts and a Bundle. AgentPlane consumes the Bundle and preserves execution-plane evidence without rescanning upstream state.

The semantic-control path is:

1. Public artifact remains public.
2. Bundle carries `spec.policy.semanticControl`.
3. Validator resolves `profileRef`.
4. Validator verifies schema, canonical hash, signature, audience, expiry, and key status.
5. Validator projects the profile into bounded runtime knobs.
6. Control gate evaluates the projection.
7. Placement, run, and replay artifacts bind the profile hash and projection.

## Doctrine rules

| ID | Rule | Operational meaning |
|---|---|---|
| BD-001 | Public artifact stays public | Public SCT/STN/SEM forms may signal lineage and intent, but cannot authorize runtime behavior. |
| BD-002 | Private means keyed, not invisible | The carrier remains visible and inspectable; the keybook/profile restricts interpretation. |
| BD-003 | Legend, commentary, execution are distinct | Motif lexicon, lineage commentary, and executable profile are separately versioned and linked. |
| BD-004 | Semaphoric form signals; sidecar authorizes | Runtime authority comes only from signed SCTControlProfile. |
| BD-005 | STN-K never talks directly to runtime | Shorthand must pass through SEM-K and signed profile projection before execution. |
| BD-006 | Unauthorized inference is telemetry, not success | U0-U3 arms may infer lineage; they must not recover privileged projection or authority. |
| BD-007 | Rupture is authority transition | Rupture / break-glass requires reason, authority class, human gate, and artifact binding. |
| BD-008 | Replay binds same hash or signed successor | Replay must use identical profile hash or an explicitly authorized successor profile. |
| BD-009 | No reward for covert drift | Agents are not rewarded for converting public artifacts into privileged action. |
| BD-010 | Valid signature is not enough | Signed/audience-valid profiles can still fail if motif-to-projection semantics are invalid. |

## Projection boundary

Profiles may project only into bounded runtime fields: `lane`, `toolBudget`, `plannerBranchBudget`, `memoryScope`, `disclosureScope`, `handoffPolicy`, `interruptPolicy`, `maxRunSeconds`, `auditMode`, `humanGateRequired`, and `breakGlassAllowed`.

Profiles may not pass interpretive prose directly into runtime.

## Disallowed controls

Runtime semantics must not depend on invisible text, invisible layout changes, ambiguous Unicode substitutions, hidden comments, or renderer-specific behavior. The carrier remains inspectable; the sidecar authorizes.
