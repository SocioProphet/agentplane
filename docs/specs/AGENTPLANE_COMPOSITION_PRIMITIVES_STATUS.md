# AGENTPLANE_COMPOSITION_PRIMITIVES — Dependency Status & Reconciliation
**Companion to:** `AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC.md`
**Audit date:** 2026-07-03 (verified against `~/dev/agentplane`, `~/dev/{SCOPE-D,policy-fabric,memory-mesh,guardrail-fabric}`)
**Purpose:** record what the spec depends on that does / does not exist, and reconcile its overlapping
primitives with `SP_TRACE_CFR_001_SPEC.md` so we build each mechanism once.

---

## 1. Dependency status (verified)

| Dependency | Status | Evidence |
|---|---|---|
| `ReceiptIR` base | ✅ EXISTS | `schemas/receipt.schema.v0.1.json` |
| StopGateArtifact spec + schema | ✅ EXISTS | `docs/StopGateArtifact.spec.v0.1.md`, `schemas/stop-gate-artifact.schema.v0.1.json` |
| SCOPE-D | ✅ EXISTS | `~/dev/SCOPE-D` (330 refs) |
| Memory Mesh | ✅ EXISTS | `~/dev/memory-mesh`, `~/dev/memorymesh` (107 refs) |
| WallGuard | ✅ EXISTS | `tools/wallguard_collaboration_gate.py` (29 refs) |
| Policy Fabric / Constitutional Policy Engine | ✅ EXISTS | `~/dev/policy-fabric` (353 refs); Constitutional (7 refs) |
| `ObligationIR` base schema | ❌ MISSING | no `obligation*.schema.json`; only a concept in the StopGate spec |
| `VerifierIR` base schema | ❌ MISSING | concept lives in `tools/stopgate_artifact.py`, no standalone schema |
| `EvidenceIR` base schema | ❌ MISSING | many concrete `*-evidence` schemas, no base `evidence.ir` |
| `ClaimIR` base schema | ❌ MISSING | (SP-TRACE-CFR WO-0.B is defining a minimal one) |
| `LedgerIR` base schema | ❌ MISSING | only `agentic-ops-budget-ledger` (a specific ledger) |
| **Mellumwork** framework (T1/T2) | ❌ NOT LOCATABLE | 0 files; the entire tiering doctrine rests on it |
| **CBES** axioms (A1–A7) | ❌ NOT LOCATABLE | 0 files; §6 `prohibition` claims "CBES axioms already express prohibitions" |

### Consequences (must resolve before the §13 deltas are buildable)
1. **The §13 "v2 deltas" amend v1 bases that do not exist for 5 of 6 IRs.** ObligationIR/VerifierIR/
   EvidenceIR/ClaimIR/LedgerIR need a **base v1 schema authored first**, then the v2 delta applied.
   Only ReceiptIR can take its v2 `fold` delta directly.
2. **§13.6 StepGateArtifact `allOf $ref "stopgate.artifact/v1"` is a dangling ref** — the base
   `stop-gate-artifact.schema.v0.1.json` has **no `$id`**. Fix: add `"$id": "stopgate.artifact/v1"`
   to the base schema (a one-line, backward-compatible change) before StepGateArtifact validates.
3. **Mellumwork and CBES are cited as normative dependencies but are not in-repo.** Either they live
   outside these repos (Documents / another estate) and must be linked, or the T1/T2 tiering and the
   `prohibition`↔CBES claim are **asserted, not grounded** — treat as such until located. (Same
   discipline that corrected SP-TRACE-CFR's GOV-IRRED-001.)

---

## 2. Reconciliation with SP-TRACE-CFR-001 (build each mechanism once)

Four primitives overlap SP-TRACE-CFR. The composition spec is the **general** mechanism; SP-TRACE-CFR
is a **consumer/specialization**. Bindings:

| Composition primitive | SP-TRACE-CFR touchpoint | Reconciliation |
|---|---|---|
| **§9 StepGateArtifact** (per-node, Tier-0/1, p95<50ms, short-circuit) | SP-TRACE-CFR Tier-0 (hammock) / Tier-1 (interval) + WO-0.C StopGate supersession | SP-TRACE-CFR **emits StepGateArtifacts**; its per-claim verdict counts + async amendment become the §9 per-node model + §13.6 artifact. **WO-0.C is subsumed by §9** — build §9 once. |
| **§8 conformal INDETERMINATE** | SP-TRACE-CFR §6 Abstention Calibration (moat metric) | SP-TRACE-CFR's ZERO/INDETERMINATE adopts §8 conformal risk control; AC becomes the §14.5 coverage test. Upgrades AC from heuristic to distribution-free. |
| **§6 ObligationIR kind system + §11 taint** | SP-TRACE-CFR WO-0.D (recommended *defer* ObligationIR); GOV-SC-DETACH; GOV-IRRED capability-class escalation | **Reverses WO-0.D defer.** GOV-SC-DETACH binds to `kind=prohibition`/`resource` pre-auth; the GOV-IRRED "crosses a capability-class boundary" escalation binds to §11 `resource.taint` labels. SP-TRACE-CFR now **consumes** the composition ObligationIR instead of deferring it. |
| **§4 receipt fold (monoid/abelian_group)** | SP-TRACE-CFR I-SC1 sidechain + StopGate §9 propagation | Sidechain verdict propagation (VIOLATION in `T[s]` → parent REVIEW) uses the §4 **monoid** (success) fold; blame attribution uses the §4 **abelian_group** fold + §10 AttributionIR. |

### Net effect on SP-TRACE-CFR WO-0
- **WO-0.C** (StopGate supersession/partial-verdict) → **replaced by** "adopt §9 StepGateArtifact + §4 fold".
- **WO-0.D** (ObligationIR: defer) → **changed to** "consume composition-spec ObligationIR v2 (§6/§11)"; GOV-SC-DETACH and O1 are **no longer deferred** once §6/§13.1 lands.
- SP-TRACE-CFR's `orch-dsl` reverse-topo fixture sampler aligns with §1 / §14.4 (shared sampler).

---

## 3. Suggested build order (folds the two specs together)
Following the spec's own §15 leverage ranking, adjusted for the missing bases:

0. **Author base v1 schemas** for ObligationIR / VerifierIR / EvidenceIR / ClaimIR / LedgerIR (or the
   minimal subsets each consumer needs). Add `$id` to the StopGate base schema. *(prerequisite; blocks §13)*
1. **§8 conformal** on the INDETERMINATE branch — highest leverage, upgrades the shared AC moat metric.
2. **§6 + §11** ObligationIR kind system + argument taint — unblocks SP-TRACE-CFR GOV-SC-DETACH/GOV-IRRED.
3. **§9 StepGateArtifact** — the unified per-node gate SP-TRACE-CFR Tier-0/1 emits into.
4. **§4 fold** + §14.1 permutation test — replay-safe sidechain aggregation.
5. **§10 AttributionIR** replay job; **§12 CINormIR**; **§7** enforcement-mode enum; **§3/§5** diagnostics.

Locate or link **Mellumwork** and **CBES** before relying on the T1/T2 tiering and `prohibition` doctrine.
