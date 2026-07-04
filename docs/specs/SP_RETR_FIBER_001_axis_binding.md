# SP-RETR-FIBER-001 — Axis Binding
**Status:** DRAFT — repo-faithful binding (2026-07-04); ratify after WO_FIBER_001 review
**Layer:** AgentPlane / retrieval + evidence-emission family
**Amends:** SP-RETR-FIBER-001 §3.3 (verdict), §3.4.4 (E-grade), §6.1–§6.4 (verdict+attestation), and every `EGrade{E0..E5}` reference
**Reconciles:** the spec's numeric `E1/E4` grades + standalone `Verdict` enum against verified repo state
**Verified against:** `agentplane/tools/narration_fidelity_verifier.py:33,36`, `agentplane/tools/conformal_gate.py:2,19-27,44`, `agentplane/tools/mellumwork.py:25`, `agentplane/tools/stopgate_artifact.py:235,314,409`, `hellgraph/crates/hg_core/src/lib.rs:160` (`ValueEnvelope.epistemic_mode`), and the sibling `SP_TRACE_CFR_001_axis_binding.md` (RATIFIED)

---

## 1. The correction

SP-RETR-FIBER-001 v0.2.0 introduced a numeric `EGrade{E0..E5}` scale and treated `Verdict{Pos,Zero,Neg}` as a standalone enum. **Neither exists in code.** Adopting them would create exactly the duplicated-status drift the SP-TRACE-CFR axis binding was ratified to prevent. Every axis this spec needs already has a home.

**Resolution (mirrors the ratified SP-TRACE-CFR binding): three axes, zero new vocabulary.**

## 2. The three-axis binding (normative)

### 2.1 Verdict axis — StopGate/VerifierIR (existing enum, already signed)
The fiber-product verdict is **not a new enum**; it is a projection into the existing `narration_fidelity_verifier` values (`POS, ZERO, NEG, INDETERMINATE`, `:33`) and their `_VERDICT_TO_FINDING` map (`:36`), consumed by `stopgate_artifact`:

| SP-RETR-FIBER (fiber product, §3.3) | verifier value | VerifierIR finding | StopGate verdict | disposition |
|---|---|---|---|---|
| non-empty (fibers agree on overlap) | `POS` | `OK` | `PASS` (permit-eligible) | permit — answer with double citation |
| empty, overlap `X_ab ≠ ∅` (provable disagreement) | `NEG` | `VIOLATION` | `FAIL` | deny — surface the contradiction witness |
| vacuous cover / missing / forced-ZERO floor (§3.4.3) | `ZERO` | `None`, gate-relevant span ⇒ `REVIEW` | `INDETERMINATE`/`REVIEW` | deny — no test possible |
| conformal descent abstained (§6.2) | `INDETERMINATE` | `None` | `INDETERMINATE` | deny-require-override — ambiguous branch |

`POS`/`NEG` carry a witness (agreeing/disagreeing pair, INV-F6); `ZERO`/`INDETERMINATE` are witnessless (both → `None` finding, no permit). Keep `ZERO` and `INDETERMINATE` **distinct in the trace** for diagnosis (no-test-possible vs abstained), even though their permit consequence is identical. Monotonicity is the existing `stopgate_artifact.degrade_verdict()` (`:235`) — PASS/FAIL may drop to REVIEW, never lift.

### 2.2 Evidence-grade axis — CTRL243.evidence {exact, sampled, verified}
Replaces `EGrade{E0..E5}`. Extraction + fiber-product grade → evidence grade, subject to the repo's `verified`-promotion gate (`policy_attestation_v1.md:47`: promotion to `verified` MUST attach durable proof material) and the Mellumwork tiers (`mellumwork.py:25`, `exact/verified→T1`, `sampled→T2`):

| Condition | CTRL243.evidence | Mellumwork tier | Promotion rule |
|---|---|---|---|
| Both endpoint extractions deterministic + fiber-product exact structural match | `exact` | T1 | deterministic; permit-eligible, no promotion needed |
| Fiber product holds **with an attached agreeing/disagreeing witness** (INV-F6) | `verified` **iff** witness attached; else `sampled` | T1 (with witness) | witness = durable proof material (same gate as SP-TRACE-CFR R_I) |
| Extraction empirical / model-derived, no witness | `sampled` | T2 | advisory; **not permit-eligible** |
| Any slot in `X_ab` below `E_floor` | forced `ZERO` (§3.4.3) | — | no grade emitted |

**`E_floor` binds to `sampled`** (reject below `sampled`). **Permit-eligible answers require `verified`.** The spec's "E4 = Michael-only promotion" (§ promotion gate) = the **`verified`-promotion gate** — the existing durable-proof-material lane, Michael-gated. There is no separate numeric ladder.

### 2.3 Provenance axis — State243.epistemic / hellgraph `EpistemicMode`
State243.epistemic real vocabulary is a provenance ladder (`hypothesis | observed | derived | verified | attested | simulated`), realized per-value as `ValueEnvelope.epistemic_mode` (`hg_core/src/lib.rs:160`).

- A retrieved, page-anchored claim is `epistemic = derived` — recovered via `descend`/`traverse`, not observed as source authorship. The `evidence.v0.anchor_ref` makes it **citable**, not `observed`.
- Promotable to `verified` when its evidence grade reaches `verified` per §2.2 (fiber-product witness attached).
- Never `attested` (no human sign-off in the retrieval path) and never `simulated`.

## 3. Consequences

1. **Delete `EGrade{E0..E5}` from the spec IR.** The `Atom.egrade` field (spec §3.4.1) binds to CTRL243.evidence `{exact,sampled,verified}`. INV-F9 (E-grade monotonicity) is re-stated over this ordering: `exact ⊒ verified ⊒ sampled` for permit purposes, and a verdict's grade ≤ `min` of endpoint extraction grades.
2. **The spec's `Verdict` type is a view, not a definition.** It re-exports the four verifier values; `descend`/`traverse` emit them through `_VERDICT_TO_FINDING` into the existing StopGate path.
3. **Double-grounding (spec §6.3)** = (provenance axis: `derived`+`anchor_ref`) × (evidence axis: `{exact,sampled,verified}` with witness). Both ride existing fields; no new attestation vocabulary.

*Ratify alongside `SP_RETR_FIBER_001_BINDING.md` after review. Where the spec's numeric grades disagree with this file, this file wins.*
