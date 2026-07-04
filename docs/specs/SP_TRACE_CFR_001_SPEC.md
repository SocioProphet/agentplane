# SP-TRACE-CFR-001 — Trace Control-Flow Recovery & Narration Structure Verification
**Version:** 0.1.0 (P0 spec; work-order basis)
**Layer:** AgentPlane / evidence-emission family
**Home:** `~/dev/agentplane` (branch `feat/trace-cfr`)
**Depends on:** `docs/StopGateArtifact.spec.v0.1.md`, `tools/stopgate_artifact.py` (VerifierIR finding→verdict→degrade→sign), the replay-record schemas (`schemas/conversational-replay-record.schema.v0.1.json`, `schemas/agentic-ops-trajectory-event.schema.v0.1.json`), `schemas/reasoning-failure-trace.schema.v0.1.json`, HellGraph append-only JSONL replay log (`~/dev/hellgraph`)
**Binds vocabulary via:** `SP_TRACE_CFR_001_axis_binding.md` (RATIFIED)
**Tier:** Tier-0 component budget p95 < 50 ms per session segment
**Build target (does not yet exist):** `tools/narration_fidelity_verifier.py`

---

## 0. Changes from the inline v0.1-draft (ratified 2026-07-03)

1. **Three-axis binding, no new vocabulary.** Verdict projects into the existing StopGate/VerifierIR
   domain; evidence grade binds to `CTRL243.evidence {exact,sampled,verified}`; provenance binds to
   `State243.epistemic {derived,verified}`. See `SP_TRACE_CFR_001_axis_binding.md`.
2. **v0.1 = two engines** (R_H hammock + R_I interval). R_PI (pattern-independent) deferred to v0.2;
   it can only ever emit `sampled` evidence and never a permit-eligible verdict, so v0.1 loses zero
   verified-grade capability. This also removes the entire synthetic-evidence contamination class
   (Rule E1) from v0.1.
3. **Decision-4 reversed.** Decision sites are keyed on the replay record's stable **site id**
   (§4.1), not a `payload_hash` prefix. Payload-hash keying could manufacture false-POS branch/loop
   structure under collision and fragments loops under data variation.
4. **P5/V1 contradiction fixed** (§4.5): sign-disagreement between the two semantic engines routes to
   `VERIFIER-FAULT-001` (INDETERMINATE); the `NEG` rows explicitly exclude the R_H=POS subcase.
5. **WHILE ≢ DO_WHILE made sound** (§4.1, §4.4): P1 records guard position relative to first body
   execution; zero-trip WHILE (no body, no backedge) recovers to ZERO, never NEG.
6. **T4 flag-only** and `threaded_suspect` caps semantic engines at ZERO on covered spans (§4.2, §4.5).
7. **Hashing = sha256 / blake2b** (stdlib), not blake3, to match the repo's zero-dependency posture.
8. **Async gate revision** defined (§5.1): a Tier-1 finding supersedes a Tier-0-sealed artifact via a
   signed amendment.

---

## 0.1 Unmet dependencies — VERIFIED prerequisites (audit 2026-07-03)

A repo audit found that several substrates this spec consumes do **not yet exist**. These are hard
prerequisites, not assumptions; each becomes an explicit work order (WO-0).

1. **The replay substrate does not emit the control-flow signal.** `agentic-ops-trajectory-event`
   carries `stepKind ∈ {model_call, tool_call, verification, memory_write, degradation, termination}`
   and a *governance* `decisions` object (`admit/reject`), but **no** `decision`(branch)/`spawn`/`join`
   step kinds, and no `site_id`, `branch_taken`, `guard_position`, `sidechain_id`, or
   `parent_event_id`. There is currently **nothing to recover a CFG from.** ⇒ WO-0 must extend the
   orchestrator + trajectory schema to emit these labels before WO-1 has any input.
2. **`ClaimIR` does not exist as a schema.** The α compiler (D5, P4) and the `covers` span have no
   defined input. ⇒ a minimal `ClaimIR` schema is a WO-0 deliverable.
3. **`ObligationIR` does not exist.** `GOV-SC-DETACH-001` pre-auth and the O1 depth rule reference it.
   ⇒ recommended: **defer both out of v0.1**; keep `GOV-SC-MULTIJOIN-001` and `GOV-IRRED-001`, which
   need no ObligationIR. (Alternative: define a minimal ObligationIR in WO-0.)
4. **StopGate has no supersession or partial-verdict aggregation.** Its spec §10 lists partial-verdict
   composition as OPEN; there is no amendment mechanism. ⇒ §5.1 and the per-claim verdict counts are
   **proposed StopGate extensions**, not conformance; they must land in the StopGate spec first.
5. **GOV-IRRED-001 ↔ the June sidechain-audit finding — CHECKED (2026-07-03): no such audit exists.**
   A `~/dev` + `~/Documents` sweep found no artifact documenting a sidechain control-flow audit; the
   only real "sidechain" concept in the estate is StopGate spec §9 (delegated-`Task` propagation). ⇒
   GOV-IRRED-001 is **reframed as a proposed detector**, motivated by StopGate §9, whose real-world
   correspondence is **validated synthetically by eval stratum S5** — not by any prior finding. It
   must not be described as codifying an audit.

---

## 1. Scope and non-goals

**In scope:** recovery of orchestration control-flow structure from AgentPlane replay logs;
verification of recovered structure against agent narration; emission of verdicts bound into
StopGateArtifacts; detection of irreducible-flow governance anomalies.

**Out of scope (v0.1):** data-flow verification (only *that* control transferred, not what values);
cross-session structure; probabilistic/ML judges; live (pre-completion) verification (post-hoc on
sealed segments only); R_PI pattern-independent recovery (deferred to v0.2).

**Forensic axiom carried over:** ZERO is not NEG. Every verdict is scoped to the exact log segment,
method, and normalization version that produced it. Vagueness is counted, never charged.

**Structural scope caveat (must be carried in the artifact):** a `POS` from this verifier attests the
**control structure** matches the claim. It is *not* an attestation of the narration's claims about
*content/values* (that is data-flow, out of scope). Consumers MUST NOT read structural-POS as
semantic-truth.

---

## 2. Definitions

**D1. Replay event (requires WO-0 emitter extension — see §0.1).** SP-TRACE-CFR consumes the control-
flow view below. `agentic-ops-trajectory-event` today supplies only `stepKind` (tool_call/termination)
and a *governance* `decisions` object; the `decision`(branch)/`spawn`/`join` kinds and the
`site_id`/`branch_taken`/`guard_position`/`sidechain_id`/`parent_event_id` fields **must be added by
WO-0**. This is an extension of the trajectory event, not a free projection. Fields consumed:
```json
{
  "event_id":        "uuid-v7",
  "session_id":      "uuid",
  "parent_event_id": "uuid-v7 | null",
  "agent_id":        "string",
  "site_id":         "string   // stable orchestration-site identity from the replay record",
  "sidechain_id":    "string | null",
  "kind":            "tool_call | tool_result | decision | spawn | join | narration | gate | terminal",
  "ts_mono_ns":      "u64",
  "payload_hash":    "sha256 hex",
  "branch_taken":    "string | null",
  "guard_position":  "pre | post | null   // decision relative to first body exec (§4.1)"
}
```
`site_id` and `guard_position` are the two control-flow fields projected onto (or extended from) the
source replay record. Records missing `event_id`, `kind`, `site_id`, or `ts_mono_ns` render the
segment `INDETERMINATE` at ingest — no repair (repair is evidence tampering).

**D2. Trace CFG.** `T = (V, E, entry, X)`:
- `V` ⊆ events with `kind ∈ {tool_call, decision, spawn, join, terminal}`. `narration` and
  `tool_result` are *annotations on* nodes; `gate` events are region boundary markers.
- `E ⊆ V×V×L`, `L = {seq, br_true, br_false, br_case(k), spawn, join, backedge?}`; `backedge` is
  *derived* (§4.2), never present in the log.
- `entry` = unique node with no incoming `seq/br_*` edge in the segment.
- `X` = set of `terminal` nodes; `|X| ≥ 1` required; `|X| > 1` is legal and must not be synthetically merged.

**D3. Sidechain subgraph.** For sidechain `s`, `T[s]` = induced subgraph plus its `spawn` in-edge and
`join` out-edge. **Invariant I-SC1:** `T[s]` is SESE relative to the parent — exactly one `spawn`
in-edge, ≤ 1 `join` out-edge. Violation ⇒ `GOV-SC-MULTIJOIN-001`, StopGate `VIOLATION`.

**D4. Primitive alphabet.**
`Π = {SEQ, IF, IF_ELSE, WHILE, DO_WHILE, LOOP_MULTI_EXIT, SWITCH, SPAWN_JOIN, SPAWN_DETACHED}`.
`SPAWN_DETACHED` is legal only with an ObligationIR pre-auth; else `GOV-SC-DETACH-001`, `VIOLATION`.

**D5. Claimed structure.** `α : ClaimIR → AST(Π)`, the deterministic compiler from narration claim
clauses to a Π-AST. Unparseable claim ⇒ `ZERO`, reason `CLAIM_UNSTRUCTURED` (counted, §10 AC metric).

---

## 3. IR schemas

### 3.1 VerifierIR extension (additive; `verifier_class: trace_cfr`)
```json
{
  "verifier_class":         "trace_cfr",
  "recovery_method":        "hammock | interval",
  "equivalence_class":      "semantic",
  "normalization_version":  "N-<semver>-<blake2b-8 of transform set>",
  "ctrl243_evidence_grade": "exact | sampled | verified",
  "state243_epistemic":     "derived | verified",
  "evidence_promotion_ref": "sha256 of durable witness | null",
  "verdict_projection":     "POS | ZERO | NEG",
  "fp_profile":             "none | bounded",
  "fn_profile":             "none | bounded | unbounded",
  "segment_ref": {
    "log_uri":        "string",
    "first_event_id": "uuid-v7",
    "last_event_id":  "uuid-v7",
    "segment_hash":   "sha256 of raw JSONL bytes, inclusive"
  }
}
```
Schema-enforced constraints (`const` per method):
- `hammock`  ⇒ `fp_profile:none`,    `fn_profile:unbounded`, `equivalence_class:semantic`, grade `exact`
- `interval` ⇒ `fp_profile:bounded`, `fn_profile:bounded`,   `equivalence_class:semantic`, grade `sampled|verified`
- `ctrl243_evidence_grade == "verified"` ⇒ `evidence_promotion_ref != null` (promotion gate)
- (v0.2) `pattern_independent` ⇒ `equivalence_class:functional`, grade `sampled` (never `verified`)

### 3.2 EvidenceIR extension
```json
{
  "evidence_kind": "cfr_witness",
  "witness_type":  "iso_match | irreducible_region | claim_mismatch",
  "node_ids":      ["uuid-v7", "..."],
  "edge_list":     [["uuid","uuid","label"], "..."],
  "synthetic":     false,
  "derivation":    "string — which transform/step produced this, e.g. 'N.T3 short-circuit-fold'"
}
```
**Rule E1:** evidence whose `node_ids` include normalization-introduced nodes MUST set
`synthetic: true`; synthetic evidence may support `REVIEW`, never `VIOLATION`. (v0.1: the only
synthetic source is T3 compound-predicate folding — deterministic and semantics-preserving.
`synthetic_condition` witnesses re-enter with R_PI in v0.2.)

### 3.3 Anomaly registry
| ID | Trigger | StopGate verdict | Evidence |
|---|---|---|---|
| `GOV-IRRED-001` | Interval derivation non-singleton; irreducible region entered other than via header | `REVIEW`; ⇒ `VIOLATION` if any non-header entry edge crosses a `sidechain_id` or ObligationIR capability-class boundary | `irreducible_region`: minimal SCC + all entry edges |
| `GOV-SC-MULTIJOIN-001` | Sidechain violates I-SC1 | `VIOLATION` | edge_list of extra join/spawn edges |
| `GOV-SC-DETACH-001` | `SPAWN_DETACHED` w/o ObligationIR pre-auth | `VIOLATION` | spawn node + null-join proof |
| `GOV-NARR-STRUCT-001` | `NEG` from a semantic-class verifier | `VIOLATION` | `claim_mismatch` + α(n) AST hash |
| `VERIFIER-FAULT-001` | Sign disagreement between R_H and R_I (§4.5 V1) | INDETERMINATE | both recovered ASTs + hashes |

---

## 4. Pipeline (five passes, strictly ordered; each emits its own hash into the StopGateArtifact)

### 4.0 P0 — Ingest & segment sealing
Read raw JSONL bytes. Compute `segment_hash` over raw bytes **before** parsing. Reject
(INDETERMINATE) on: non-monotone `ts_mono_ns` within an `agent_id`, duplicate `event_id`, dangling
`parent_event_id`, or a record missing `site_id`. No repair.

### 4.1 P1 — CFG construction
- Nodes/edges per D2. `branch_taken` on a `decision` node's successor determines edge label.
- **Latent branch:** a decision node observed with only one out-edge across the segment records
  `latent_arms ≥ 1`. Recovery MUST NOT conclude `SEQ` from a single-execution decision node (dynamic
  trace ≠ static CFG — the primary soundness disanalogy vs. static decompilation).
- **Site keying:** decision executions fold into one node **by `site_id`** (stable orchestration-site
  identity from the replay record), carrying a multiset of taken labels. NOT keyed on payload — same
  site with different data stays one node; different sites never collide.
- **Guard position (WHILE vs DO_WHILE):** for each loop site, record `guard_position`:
  `pre`  = guard `decision` precedes first body node (WHILE);
  `post` = first body node precedes guard `decision` (DO_WHILE).
  If unresolved for a site ⇒ that loop is ZERO, not NEG.
- **Zero-trip WHILE:** a WHILE that runs zero times leaves no body node and no backedge; it appears as
  `decision→follow`. A truthful "while (0 times)" claim over such a span recovers to **ZERO**, never NEG.

### 4.2 P2 — Normalization N (versioned, ordered, semantics-preserving)
`N = [T1..T5]` to fixpoint in order; `normalization_version = blake2b-8(canonical serialization of the
transform list)`. Changing order = new version.
- **T1 empty-node elision:** remove pure `seq` pass-throughs (in-deg 1, out-deg 1, no side-effect flag).
- **T2 chain compression:** maximal `seq` chains → single SEQ region node (keeps member list).
- **T3 short-circuit folding:** canonical `a && b`, `a || b` shapes → single decision node with a
  compound predicate tree `⟨a ∘ b⟩` (recorded as trees, not strings). Introduced nodes ⇒ E1 synthetic.
- **T4 jump-thread unfolding:** **flag-only in v0.1.** If a decision site's taken-label sets are
  exactly (not statistically) partitioned by an earlier decision's label (dominator + label
  correlation), annotate `threaded_suspect: true`. No split. A `threaded_suspect` node caps the
  semantic engines at ZERO on any claim covering it (see §4.5).
- **T5 backedge derivation:** DFS from entry; retreating edges to a dominator = `backedge`.
  Non-dominating retreating edges stay `retreat_nondom` — the raw material of GOV-IRRED-001.

### 4.3 P3 — Recovery (two engines in v0.1)

**R_H (hammock, Tier-0, evidence grade `exact`).** Pattern library `Π_H` of exact canonical subgraphs
(SEQ, IF, IF_ELSE, WHILE, DO_WHILE, SWITCH, SPAWN_JOIN); bottom-up innermost-region collapse to
fixpoint. **Latent-branch rule:** a node with `latent_arms ≥ 1` matches only
`DECISION_OBSERVED_PARTIAL`, contribution ZERO — never IF/IF_ELSE. Patterns ≤ 4 nodes; rooted matching
from each decision/spawn node ⇒ O(|V|·k), no general subgraph isomorphism. Terminates at single node ⇒
full recovery; residual ⇒ per-region partial recovery + ZERO for uncovered regions. `fp_profile:none`.

**R_I (interval, Tier-1, evidence grade `sampled`→`verified` with witness).** Allen–Cocke derived
sequence G¹…Gⁿ on the post-N graph. Singleton `Gⁿ` ⇒ reducible; extract loop nesting from interval
headers with backedges, follow nodes per Cifuentes. Non-singleton fixpoint ⇒ irreducible: compute
limit-graph SCCs; each SCC with ≥ 2 entry nodes emits `GOV-IRRED-001` (SCC set + all entry edges +
their `sidechain_id`s). This detects a sidechain edge entering a loop body not through its header — a
**proposed** governance signal motivated by StopGate §9 delegated-`Task` semantics and validated by
eval stratum S5 (§0.1.5); it does **not** codify a documented audit. Exports `nesting_depth(v)` for ObligationIR
scoping rule **O1** (an obligation opened at depth d discharges at depth ≤ d within the same interval
or is carried via a `join` node; violation ⇒ `REVIEW`). The interval witness (SCC + entry edges +
nesting) is the durable proof material that promotes evidence to `verified` (axis binding §2.2).

*(v0.2: R_PI pattern-independent — reaching-conditions per Yakdan; `functional` equivalence; grade
`sampled`, never promotable; contributes REVIEW-downgrades only.)*

### 4.4 P4 — Claim comparison
For each narration event with parseable ClaimIR: compute `α(nᵢ)`; locate its span (claim MUST carry
`covers:[first_event_id,last_event_id]`; absent ⇒ ZERO, `CLAIM_UNANCHORED`); compare against each
engine's recovered AST restricted to that span.
Comparison relation = AST equality up to **only** (a) SEQ associativity, (b) SWITCH case order,
(c) IF arm swap **with predicate negation**. Branch guards are **identity-compared** (an un-negated
arm swap is NEG). In particular **WHILE ≢ DO_WHILE** (pre-check vs post-check is a real fidelity
failure), subject to the guard-position and zero-trip rules of §4.1.

### 4.5 P5 — Verdict composition → VerifierIR finding (per claim)
Composite maps to a VerifierIR finding, consumed by the existing `stopgate_artifact.emit` path (axis
binding §2.1). `threaded_suspect` on any covered node caps R_H and R_I contributions at ZERO first.

| R_H | R_I | Composite | VerifierIR finding → StopGate |
|---|---|---|---|
| POS | POS | POS (verified if R_I witness) | NONE → PASS / OK |
| POS | ZERO | POS (exact) | NONE → PASS / OK |
| ZERO | POS | POS | NONE → PASS / OK |
| ZERO | ZERO | ZERO | NONE → INDETERMINATE (REVIEW iff gate-relevant span) |
| ZERO | NEG | NEG | VIOLATION → FAIL (`GOV-NARR-STRUCT-001`) |
| NEG | ZERO | NEG | VIOLATION → FAIL (`GOV-NARR-STRUCT-001`) |
| NEG | NEG | NEG | VIOLATION → FAIL |
| **POS** | **NEG** | **INDETERMINATE** | **VERIFIER-FAULT-001** (see V1) |
| **NEG** | **POS** | **INDETERMINATE** | **VERIFIER-FAULT-001** (see V1) |

**V1 (monotonicity + self-check).** The two semantic engines can only be overruled *toward* caution
(via `degrade_verdict`), never toward POS. A **sign disagreement** between R_H and R_I (one POS, one
NEG) is impossible if both are correct — it is a harness fault, not a lying agent: emit
`VERIFIER-FAULT-001`, verdict INDETERMINATE, **never** charge a VIOLATION off a self-inconsistent
harness. This resolves the draft's P5/V1 contradiction: the `NEG` rows above exclude the R_H=POS and
R_I=POS subcases, which route here instead.

---

## 5. StopGateArtifact binding

Per sealed segment, the **harness** (not the model — §5.1 model-exclusion of the StopGate spec) emits a
subject-scoped StopGateArtifact via `tools/stopgate_artifact.py`, carrying `segment_ref`,
`normalization_version`, `engine_versions`, per-verdict counts, anomaly refs, `evidence_hashes`, and
the `ed25519` `harness_sig`. No new signing machinery; the three-axis fields (§3.1) ride in the
VerifierIR record. **Structural-scope caveat (§1) is carried as an artifact field** so consumers do
not over-read POS.

**Sidechain propagation** (inherits StopGate spec §9): a `VIOLATION` in `T[s]` propagates to the parent
gate as `REVIEW` minimum; `GOV-SC-*` classes propagate as `VIOLATION` unattenuated.

### 5.1 Async gate revision (PROPOSED StopGate extension — resolves StopGate spec §10 open item)
**Prerequisite (§0.1.4):** StopGate has no supersession/partial-verdict aggregation today; this section
must land in the StopGate spec before it is conformant.
Tier-0 (R_H only) has `fn_profile:unbounded`: a segment may seal OK on hammock and later have R_I find
`GOV-IRRED-001`. The Tier-0 artifact is **not mutated**. R_I emits a **signed amendment artifact** that
references the Tier-0 artifact's hash and supersedes its verdict (monotone toward caution only — an
amendment may lower PASS→REVIEW/FAIL, never lift). Consumers resolve to the latest non-superseded
artifact for a given `segment_ref`.

### 5.2 NEG output emits a ReasoningFailureTrace
A `NEG` composite additionally emits a `ReasoningFailureTrace` (existing schema) with
`verifier_decision`, `claim_refs`, the α(n) AST hash, and `inter_agent_alignment` populated — rather
than a bespoke mismatch object.

---

## 6. Fixture strata — `SP-EVAL-TRACE-CFR-001`

Ground truth = authored orchestration programs in `orch-dsl` (see `orch_dsl_grammar.md`), executed
deterministically to produce replay logs; the DSL AST *is* the ground-truth structure. Per stratum
≥ 15 instances; scored FP/FN per primitive per engine + composite accuracy.

| Stratum | Contents | Kills |
|---|---|---|
| S1 canonical | each Π primitive, isolated + nested depth 3 | baseline |
| S2 multi-exit | break/continue depths 1–3 | hammock FN accounting; interval follow-node logic |
| S3 short-circuit | `&&`/`||` length 2–4 | T3 correctness |
| S4 threaded | decision reuse, truthful narration | composite must be ZERO/POS — **any NEG is a release blocker** (false accusation) |
| S5 irreducible | non-header loop entries incl. cross-sidechain | GOV-IRRED-001 precision/recall, **FP = 0** target |
| S6 sidechain | I-SC1 violations, detached spawns, obligation-scoped spawns | GOV-SC-* |
| S7 latent | single-execution decision sites | latent-branch rule: composite ZERO, **never POS** |
| S8 lying narration | truthful trace, claim off by one primitive (WHILE claimed / DO_WHILE run; IF / IF_ELSE; seq / spawned) | **NEG recall ≥ 0.95 semantic** at FP ≤ 0.02 |
| S8z zero-trip loops | truthful "while (0 times)" | must be ZERO, **never NEG** (guard against the zero-trip trap) |
| S9 vague narration | unparseable/unanchored claims | ZERO discipline; AC denominator |

**Abstention Calibration (moat metric, shared harness with SP-EVAL-CRF-001):**
AC = P(ZERO | genuinely undecidable from trace) vs P(ZERO | decidable); report both; the gap is the score.

**Acceptance criteria v0.1:** S4 NEG = 0; S8z NEG = 0; S5 GOV-IRRED-001 FP = 0 & recall ≥ 0.9;
S8 semantic NEG recall ≥ 0.95 at FP ≤ 0.02; Tier-0 (P0–P3.R_H) p95 < 50 ms on segments ≤ 2,000 events.

---

## 7. Explicit v0.1 exclusions (do not gold-plate)
No R_PI. No T4 unfolding (flag only). No cross-session merging. No malformed-log repair. No statistical
branch inference. No LLM judge anywhere in this pipeline — deterministic engines only.

---

## 8. Work-order decomposition (two-command-pair discipline)
- **WO-0 (unmet prerequisites, §0.1) — BLOCKS WO-1:** extend `agentic-ops-trajectory-event` +
  orchestrator to emit control-flow labels (decision/spawn/join kinds, `site_id`, `branch_taken`,
  `guard_position`, `sidechain_id`, `parent_event_id`); define minimal `ClaimIR`; land the StopGate
  supersession/partial-verdict extension; decide ObligationIR (defer GOV-SC-DETACH/O1 vs define);
  ground GOV-IRRED-001 against the real audit findings.
- **WO-1 (P0–P2 harness):** `tools/trace_cfr/{ingest,cfg,normalize}.py` + `schemas/trace-cfr-segment.schema.v0.1.json` + replay-record extension + `tools/tests/test_trace_cfr_harness.py`.
- **WO-2 (R_H, Tier-0):** `tools/trace_cfr/recover_hammock.py` + Π_H + `tools/trace_cfr/bench_tier0.py` + tests.
- **WO-3 (R_I, Tier-1 + anomalies + amendment):** `tools/trace_cfr/recover_interval.py` + §5.1 amendment + tests.
- **WO-4 (P4/P5 + binding):** `tools/narration_fidelity_verifier.py` + `tools/validate_narration_fidelity.py` (VerifierIR finding → `stopgate_artifact.emit`; NEG → ReasoningFailureTrace) + tests.
- **WO-5 (eval):** `tools/orch_dsl/` interpreter + strata S1–S9(+S8z) + AC harness.

All Python stdlib-only (repo zero-dependency posture; `ed25519_pure` precedent). Each WO lands with its
`validate_*.py` and `tools/tests/test_*.py` pair. P0 (this spec + axis binding + grammar) lands and is
reviewed before any engine.
