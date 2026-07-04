# WO-0 — Unmet Prerequisites for SP-TRACE-CFR-001
**Version:** 0.1.0
**Status:** work order — BLOCKS WO-1..5
**Parent:** `SP_TRACE_CFR_001_SPEC.md` §0.1, §8
**Home:** `~/dev/agentplane` (branch `feat/trace-cfr`)

WO-0 exists because a repo audit (SPEC §0.1) found that the substrates SP-TRACE-CFR consumes do not
yet exist. No recovery engine can run until these land. Five deliverables, each with its own
build+validate command pair.

> **Reconciled with `AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC.md` (see its STATUS companion §2):**
> WO-0.C is **subsumed by** that spec's §9 StepGateArtifact + §4 fold. WO-0.D **no longer defers**
> ObligationIR — it now consumes that spec's §6/§11 ObligationIR. Both changes are marked inline below.

---

## WO-0.A — Control-flow emitter extension (the input the engines recover from)

### The gap
`agentic-ops-trajectory-event` today carries `stepKind ∈ {model_call, tool_call, verification,
memory_write, degradation, termination}` and a *governance* `decisions` object (`admit/reject`). It
does **not** carry the control-flow signal a CFG needs.

### Scoping discovery (shapes what is recoverable)
Agent orchestration control flow is not uniform:
- A **linear agent loop** (model → tool → model → …) has **no static branches**. Its only recoverable
  structure is `SEQ` and, where it spawns subagents, `SPAWN_JOIN`. The IF/WHILE/SWITCH machinery is
  **dormant** for such traces — correctly recovering `SEQ`/`SPAWN_JOIN` is the whole job.
- **Graph / workflow orchestration** (conditional plans, routers, loops-with-guards) is where
  `decision`/`branch_taken`/`guard_position` become live.
WO-0.A must emit both, but v0.1's realistic first target is **SPAWN_JOIN + SEQ** from the linear loop
(that alone exercises I-SC1 / GOV-SC-MULTIJOIN / GOV-SC-DETACH and the sidechain path); branch/loop
recovery is exercised primarily by the `orch-dsl` fixtures until graph orchestration emits decisions.

### Deliverable
Extend the trajectory schema (additive) and the governed runner to emit:
| Field | Source | Notes |
|---|---|---|
| `stepKind += {decision, spawn, join}` | runner | `spawn` = subagent/`Task` call; `join` = its return; `decision` = graph-orchestration branch |
| `site_id` | runner | stable orchestration-site identity (workflow node id / call-site); the P1 fold key |
| `parent_event_id` | runner | causal parent (already implicit in trajectory ordering) |
| `sidechain_id` | runner | the `Task`/subagent id for delegated work |
| `branch_taken` | runner | edge label on a `decision` successor (graph orch only) |
| `guard_position` | runner | `pre`/`post` for loop guards (graph orch only) |

- Build: schema patch + runner emission + fixtures.
- Validate: `tools/validate_agentic_runtime_state.py`-style validator + `tools/tests/test_trace_cfr_emitter.py`.

---

## WO-0.B — Minimal `ClaimIR` schema (the α-compiler input)

### The gap
`ClaimIR` is referenced by SPEC D5/P4 but does not exist as a schema.

### Deliverable — `schemas/claim-ir.schema.v0.1.json`
```json
{
  "claim_id":  "uuid",
  "narration_event_id": "uuid-v7",
  "covers":    ["first_event_id", "last_event_id"],   // absent ⇒ ZERO CLAIM_UNANCHORED
  "clause":    { "primitive": "SEQ|IF|IF_ELSE|WHILE|DO_WHILE|SWITCH|SPAWN_JOIN|SPAWN_DETACHED",
                 "children": [ "<clause>", "..." ],
                 "guard_ref": "string | null" },        // predicate identity for P4 comparison
  "raw":       "string"                                  // the natural-language narration span
}
```
`α : ClaimIR → AST(Π)` is the deterministic compiler over `clause`. Unparseable `clause` (or a `raw`
that yields no `clause`) ⇒ `ZERO / CLAIM_UNSTRUCTURED`. Branch `guard_ref`s are identity-compared in
P4 (SPEC §4.4), so an un-negated arm swap is NEG.
- Build: schema + `α` compiler in `tools/narration_fidelity_verifier.py` (WO-4).
- Validate: `tools/validate_claim_ir.py` + tests over the `orch-dsl` narration channel.

---

## WO-0.C — StopGate supersession + partial-verdict extension  *(SUBSUMED by COMPOSITION §9 + §4)*

> Build the general mechanism once: adopt `AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC` §9 StepGateArtifact
> (per-node signed gate, Tier-0/1, supersession) and §4 fold (monoid success / abelian-group blame).
> SP-TRACE-CFR **emits StepGateArtifacts** rather than a bespoke amendment. The design below is retained
> as the requirements this must satisfy.

### The gap
StopGate spec §10 lists partial-verdict composition as OPEN; there is no amendment/supersession. SPEC
§5.1 and the per-claim verdict counts depend on both.

### Deliverable — patch `docs/StopGateArtifact.spec.v0.1.md` + `schemas/stop-gate-artifact.schema.v0.1.json`
1. **Subject-scoped verdicts:** a `subject` may carry per-item verdicts with a defined aggregation =
   the most-cautious verdict over the set (FAIL > REVIEW > INDETERMINATE > PASS). Monotone toward caution.
2. **Amendment artifact:** `supersedes: <prior artifact hash>`; an amendment may only lower a verdict
   (PASS→REVIEW/FAIL), never lift; consumers resolve to the latest non-superseded artifact per
   `segment_ref`. Reuses the existing `ed25519` signing path.
- Build: spec + schema patch.
- Validate: extend `tools/tests/test_stopgate_artifact.py`; add supersession + aggregation cases.

---

## WO-0.D — ObligationIR: CONSUME COMPOSITION §6/§11  *(was: defer — reversed)*

`ObligationIR` does not exist as a base schema, but `AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC` §6 now
makes it a first-class kind system (`goal|prohibition|softgoal|task|resource`) with §11 argument
taint. SP-TRACE-CFR **binds to that ObligationIR** instead of deferring:
- `GOV-SC-DETACH-001` pre-auth = an ObligationIR `kind ∈ {prohibition, resource}` check (§6). No longer
  deferred; charged once §6/§13.1 lands. Until then: `SPAWN_DETACHED` → `REVIEW` (pending ObligationIR).
- `GOV-IRRED-001`'s "crosses a capability-class boundary" escalation = a §11 `resource.taint` label
  crossing. Binds directly.
- O1 obligation-depth: emit `nesting_depth` as evidence now; the depth-scoping `REVIEW` activates when
  ObligationIR carries the discharge rule.
- Prerequisite: author the ObligationIR **base v1** schema (STATUS §1.1) before the §6 v2 delta applies.

---

## WO-0.E — Ground GOV-IRRED-001 — RESOLVED

Checked (SPEC §0.1.5): no sidechain-audit artifact exists. GOV-IRRED-001 stays as a **proposed**
detector, validated synthetically by eval stratum S5. No further grounding action; the spec wording is
already corrected. If a real audit surfaces later (forensic corpus / Documents), revisit S5's
ground-truth to include the observed instances.

---

## Sequencing
```
WO-0.A (emitter)  ──┐
WO-0.B (ClaimIR)  ──┼─► WO-1 (harness) ─► WO-2 (R_H) ─► WO-3 (R_I) ─► WO-4 (verifier+binding) ─► WO-5 (eval)
WO-0.C (StopGate) ──┘        (WO-0.C also gates WO-3's amendment + WO-4's binding)
WO-0.D (defer)    ── decision only, no build
WO-0.E (resolved) ── no build
```
WO-0.A and WO-0.B are the true blockers on WO-1. WO-0.C gates WO-3/WO-4. All Python stdlib-only.
