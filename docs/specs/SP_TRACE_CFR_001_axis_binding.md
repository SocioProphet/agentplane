# SP-TRACE-CFR-001 — Axis Binding & TriTRPC Reconciliation
**Status:** RATIFIED — repo-faithful binding (2026-07-03)
**Layer:** AgentPlane / evidence-emission family
**Amends:** SP-TRACE-CFR-001 §3.1 (VerifierIR extension), §8.3 (verdict), §4.5 (P5 composition)
**Reconciles:** GKG-CODEX↔TriTRPC addendum §16.4 against verified repo state of `~/dev/tritrpc @ main`
**Verified against:** `tritrpc_vnext_mini_spec.md:28`, `cskg_vnext_profile.md:45`, `policy_attestation_v1.md:38,47`, `atlas_event_v1.md:43`, `tritrpc_fips_braided_addendum.md:222`, `tritrpc_unified_v4_master_spec.md §8.4`, `beacon_delta_semantic_v1.md`

---

## 1. The correction to addendum §16.4

§16.4 asserts `verdict → State243.epistemic` with values `{INTACT/lawful→POS, compound/unknown→ZERO, tamper/corruption→NEG}`.
Repo reality: `State243.epistemic` is a **provenance ladder** — `hypothesis | observed | derived | verified | attested | simulated`. It is not a lawful/tamper verdict.

Binding a fidelity *verdict* onto `State243.epistemic` therefore *is* the duplicated-status
drift §16.4 exists to prevent. The verdict already has a home: the StopGate/VerifierIR domain.

**Resolution (ratified): three axes, zero new vocabulary.**

## 2. The three-axis binding (normative)

### 2.1 Verdict axis — StopGate/VerifierIR (unchanged, already signed)
Per-claim `POS/ZERO/NEG` is **not a standalone enum**; it is a deterministic projection into the
existing VerifierIR finding domain, consumed by the existing `stopgate_artifact.emit` path:

| SP-TRACE-CFR per-claim | VerifierIR finding | StopGate verdict | disposition |
|---|---|---|---|
| `POS` | `NONE` (no violation) | `PASS` (permit-eligible) | permit |
| `ZERO` | `NONE`, gate-relevant span ⇒ `REVIEW` | `INDETERMINATE`/`REVIEW` | deny-require-override / deny-pending-human |
| `NEG` (semantic engine) | `VIOLATION` | `FAIL` | deny |
| `NEG` (functional only) | `REVIEW` | `REVIEW` | deny-pending-human |

V1 monotonicity is **already implemented** as `stopgate_artifact.degrade_verdict()` (§5.3/5.4:
PASS/FAIL may drop to REVIEW, never lift). The functional engine is a degrade input, not new machinery.

### 2.2 Evidence-grade axis — CTRL243.evidence {exact, sampled, verified}
Recovery engine → evidence grade, subject to the repo's `verified`-promotion gate
(`policy_attestation_v1.md:47`: promotion to `verified` MUST attach durable proof material):

| Engine | fp/fn profile (spec §3.1) | CTRL243.evidence | Promotion rule |
|---|---|---|---|
| R_H hammock | fp none / fn unbounded | `exact` | deterministic formal match; no promotion needed |
| R_I interval | fp bounded / fn bounded | `verified` **iff** interval witness attached; else `sampled` | witness (SCC + entry edges + nesting) = durable proof material |
| R_PI pattern-independent | fp unbounded / fn none | `sampled` | **never promotable** (synthetic conditions ≠ proof material) |

Consequence: R_PI contributes no `verified`-grade evidence and no permit-eligible verdict ⇒
**v0.1 = {R_H, R_I}** (R_PI deferred to v0.2) loses zero verified-grade capability.

### 2.3 Provenance axis — State243.epistemic (its real vocabulary)
Every recovered structure is `epistemic = derived` (recovered from a trace, not observed as source
code), promotable to `verified` when its evidence grade reaches `verified` per 2.2. Never `attested`
(no human sign-off in this pipeline) and never `simulated`.

## 3. VerifierIR extension delta (replaces spec §3.1 fp/fn-only fields)
Additive fields on the `trace_cfr` VerifierIR record:
```json
{
  "ctrl243_evidence_grade": "exact | sampled | verified",
  "state243_epistemic":     "derived | verified",
  "evidence_promotion_ref": "hash of durable witness | null",
  "verdict_projection":     "POS | ZERO | NEG"
}
```
Schema constraint: `ctrl243_evidence_grade == "verified"` ⇒ `evidence_promotion_ref != null`
(mirrors `policy_attestation_v1` promotion gate; rejected at schema level, not policy level).

## 4. What is NOT in scope of this binding
- §16.1/16.2/16.3/16.5 (profile allocation, marker-band parity, topic23.v1, scanner hardening) are
  GKG-CODEX's critical path. SP-TRACE-CFR emits StopGateArtifacts, not TritPack243 wire bytes, so it
  is not gated on them.
- Full pipeline corrections live in `SP_TRACE_CFR_001_SPEC.md` (this doc governs only the axis binding).
