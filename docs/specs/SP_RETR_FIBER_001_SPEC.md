# SP-RETR-FIBER-001 — Fibered Retrieval over HellGraph
### companion: SP-ADAPT-TREE-001 — Structural (PageIndex-class) Ingestion Adapter

**Version:** 0.2.0 (DRAFT — public-review stop point pending WO_FIBER_001 binding)
**Layer:** AgentPlane / retrieval + evidence-emission family
**Home:** `~/dev/agentplane` (branch `spec/retr-fiber-001`)
**Evidence grade at author time:** `E1` — design-level; architecture reasoned from estate memory, **not** a fresh repo read.
**Promotion gate:** `E4` requires Michael-only sign-off (mirror SCOPE-D E4/E5/E6 lane).
**Depends on:**
- `docs/specs/AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC.md` — conformal abstention IR guard (reuse, do not reimplement)
- `docs/specs/SP_TRACE_CFR_001_SPEC.md` + `tools/stopgate_artifact.py` — StopGate/VerifierIR verdict→degrade→sign; Episode emission
- `Mellumwork` ternary verdict algebra + Episode schema (present in `docs/`, `tools/`)
- HellGraph `hg_read_kernel` (`~/dev/hellgraph`) — typed relational adjacency. **BINDING TARGET**, not a claim about current code.
- `DatasetCatalogEntry v1` — ingestion adapter contract. **BINDING TARGET; name did not grep-match in-estate on authoring, treat as unverified until WO_FIBER_001.**
- `WallGuard` — per-node visibility / consent lattice.

**Binds vocabulary via:** `SP_RETR_FIBER_001_axis_binding.md` (TODO — emit in WO_FIBER_001, mirror the RATIFIED `SP_TRACE_CFR_001_axis_binding.md`: verdict→StopGate/VerifierIR domain, evidence grade→`CTRL243.evidence`, provenance→`State243.epistemic`).
**Feeds:** `SP-EXPORT-LD-001` (HellGraph LD projection); Nasdaq beneficial-ownership delegation-chain visualization (GLEIF Level-2).
**Build target (does not yet exist):** composite-graph `EdgeClass` schema (`E^⊑ ⊔ E_R`); `descend`/`traverse` composition primitives; fiber-product verdict + Episode engine; PageIndex-class `TreeAdapter`.
**Consumer:** SocioProphet Claude Code agent (one WO per PR, narration-fidelity-verified transcripts).

---

## 0. Changes from the inline v0.1.0 draft (this revision, ratified for landing)

Five review holes in the v0.1.0 inline draft are closed:

1. **§3.3.0 (new) — the sheaf/Čech language is notation, not a mechanism.** The engine is a constraint join; the topology buys precision-of-statement and the three-value justification, and **zero** computational content beyond "compute a join, test non-emptiness." Directive: *compute the fiber product (§3.4), not a cohomology group.*
2. **§3.4 (new) — claim-variable semantics specified.** The previously-undefined `shared_claim_vars` / `restrict` / `fiber_product` are now a real extraction + alignment contract (typed claim atoms over GLEIF/FIBO/canonical-measure namespaces), E-graded, with a **forced-ZERO floor** (§3.4.3). This section — not the topology — is the actual weight of the build.
3. **§6.2 — conformal abstention is now an earned guarantee**, not a label: explicit APS nonconformity score, split-conformal calibration set + quantile, Mondrian (group-conditional) strata answering "every ToC is its own distribution," and a recalibrate-on-shift clause. INV-F5 now requires *measured* empirical coverage.
4. **§9 — cost model corrected:** frontier fan-out `b^{H_max}`, a governed beam cap `K` (new INV-F10), an explicit plan-synthesis term `C_plan` (§4.3), and the "strictly better" claim made explicitly **conditional on `E_R` precision `P_R`**.
5. **§6.3 / WO_FIBER_008 — abstention rate is a first-class metric.** The INV-F3×INV-F5 interaction (mid-descent abstention ⇒ unanchored endpoint ⇒ path ZERO) means the eval must report abstention rate + empirical coverage, or the system can be "never wrong" by being "usually ZERO."

This revision closed the *reasoning* holes; it did **not** add repo grounding. That is still WO_FIBER_001's job, and every interface above is a binding target.

---

## 0.5 Agent execution protocol (read before building)

This document is written **to** the Claude Code agent, not about it.

1. **Bind before build.** Do not implement any type below from this spec's pseudocode. Execute `WO_FIBER_001` first: read the real repo interfaces, emit `BINDING.md` mapping every spec symbol (§3.4, §4, §5) to the actual `hg_read_kernel` / `DatasetCatalogEntry v1` / `WallGuard` / `Mellumwork` type. Every later WO imports from `BINDING.md`, never from this spec's illustrative Rust.
2. **One work order, one PR.** WOs are dependency-ordered (§7). Do not open `WO_FIBER_00N+1` until `N` merges.
3. **Halt on ungraded ZERO.** If any acceptance probe returns `Verdict::Zero` for a reason other than the intended abstention / vacuous-cover / extraction-floor cases (§3.4, §6, INV-F5/F6/F9), stop and surface — do not paper over it to make a test pass.
4. **Attestation is not optional.** Every retrieval path that reaches a Narrative emits a Mellumwork Episode via `STOPGATE` (§6.4). A path with no Episode is a failed path, not a fast path.
5. **Scope findings to conditions.** The forensic-methodology rule applies to evals: an eval that did not exercise a condition is not evidence about that condition. State the corpus/condition each number was produced under. **Coverage numbers are only valid on the distribution they were calibrated against (§6.2).**

---

## 1. Objective

Fuse structural (tree) document indexing with relational (graph) retrieval into a single **fibered** substrate, so that:

- **within a document**, retrieval is a precise root→leaf walk of the author's own containment structure (the PageIndex-class contribution — exact page/section citation, no chunking, no embedding);
- **across documents**, retrieval is a typed multi-hop join over `hellgraph` relational edges (the substrate contribution — the many-to-many topology a containment tree structurally cannot represent);
- **every answer** is doubly grounded (provenance-of-location + provenance-of-claim) and carries a Mellumwork ternary verdict with an E-grade.

Target regime: multi-hop relational retrieval **with** exact per-hop citation — e.g. beneficial-ownership delegation over GLEIF Level-2 records, where each entity is anchored in a different filing and the ownership edges cross documents.

### 1.1 Out of scope
- Replacing embedding retrieval globally. Embedding ANN remains a valid *coarse candidate generator* where deterministic sublinear recall matters; this spec does not delete it, it subordinates document-internal location to tree descent.
- Multi-document *tree merging* into one synthetic root. We connect trees by relational edges (§4), not by re-rooting.
- Open-domain claim extraction. §3.4 specifies extraction only against a typed relation vocabulary (FIBO + registered predicates). Claims outside the vocabulary are `ZERO` by construction, not silently dropped or guessed.

---

## 2. The structural insight (why this composes at all)

A PageIndex tree is single-parent, containment-only (mereological `⊑`). `hellgraph` is multi-relational, many-to-many. A tree is a **degenerate special case** of a typed graph. So the fusion is not two systems bolted together; it is one graph carrying **two edge classes of opposite topology**:

- **Vertical** `E^⊑` — containment, single-parent, per-document → *the trees*. Gives structural context and page anchors.
- **Horizontal** `E_R` — typed relational, DAG-or-worse → *the connective tissue*. Gives cross-document joins the tree has no type for.

**The tree is the structural context; the graph is the connective tissue.** PageIndex output stops being a throwaway private per-document index and becomes the containment subgraph of `hellgraph`.

---

## 3. Formal model

### 3.1 The composite graph `H`

For each governed document `d`, the adapter (§5) produces a containment tree

```
T_d = (V_d, E_d^⊑),   E_d^⊑ ⊆ V_d × V_d   (single-parent, rooted at r_d, leaves page-anchored)
```

Weld via an injection `ι_d : V_d ↪ V` (tree nodes become first-class hellgraph vertices). Then

```
H = ( V , E^⊑ ⊔ E_R )
E^⊑ = ⋃_d ι_d(E_d^⊑)      -- vertical, a forest
E_R  = typed relational edges  -- horizontal, many-to-many
```

`E^⊑` and `E_R` are a **disjoint** edge classification: no edge is both.

### 3.2 The fibration

Project `π : H → B` onto the base `B = (entities, E_R)`. The fiber over an entity `e`,

```
π⁻¹(e) = { tree-node locations across all T_d that evidence e }
```

is the set of document-tree positions where `e` is witnessed. Retrieval alternates **base moves** (`traverse` along `E_R`) with **fiber moves** (`descend` along `E^⊑` inside one `T_d`). `traverse` is the coarse deterministic router *between* documents; `descend` is the fine LLM locator *within* one. Neither performs the other's job.

### 3.3 Cross-document consistency as a constraint-gluing condition (verdict semantics)

#### 3.3.0 What the math is and is not (read before implementing)

The verdict engine is a **constraint join**: given two document locations that a relational edge claims are related, extract the constraints each asserts over their shared variables and test whether those constraints have a common solution. That is the whole mechanism.

The sheaf / fiber-product / Čech language below is **notation for that test, not a second mechanism.** It buys precision of *statement* (it makes "consistent", "contradiction", and "no test possible" formally distinct rather than vibes) and it buys the honest justification for exactly-three verdict values. It buys **no** computational content beyond "compute a join, test non-emptiness." Do not implement a cohomology group; implement §3.4's `fiber_product`. The `Ȟ¹` remark (§3.3.2) is intuition only and is explicitly non-normative.

#### 3.3.1 The verdict as a fiber product

Fix a relational edge `e ∈ E_R` connecting a node in fiber `T_a` to one in fiber `T_b`. Let `X_ab` be the set of **shared claim-variables** the edge asserts a relation over (the overlap of the two fibers' evidenced claims; construction in §3.4). Let `F(·)` be the constraint presheaf: `F(n)` = the set of satisfying assignments to the claim-variables evidenced at node `n`. Restriction maps

```
ρ_a : F(a) → F(X_ab),   ρ_b : F(b) → F(X_ab)
```

send a local assignment to its trace on the overlap. The **compatibility locus** is the fiber product (equalizer of the two restrictions):

```
F(a) ×_{F(X_ab)} F(b) = { (s_a, s_b) : ρ_a(s_a) = ρ_b(s_b) }
```

The Mellumwork ternary verdict is exactly the status of this fiber product:

```
POS   ⟺  fiber product NON-EMPTY            -- a global section glues; fibers agree on overlap
NEG   ⟺  X_ab ≠ ∅  AND  fiber product EMPTY -- overlap exists, sections provably disagree (obstruction witness)
ZERO  ⟺  X_ab = ∅  (vacuous cover: no shared variable, no test possible)
          OR restriction undefined (missing/ungraded evidence — see §3.4 forced-ZERO)
          OR conformal abstention fired upstream (§6.2)
```

POS/ZERO/NEG is not an arbitrary three-valued logic bolted on — it is `{ consistent global section / obstruction / no-test-possible }`, the three states of a gluing condition on a constraint presheaf. Each `POS`/`NEG` **must** carry a witness (the agreeing pair, or the disagreeing pair); only `ZERO` may be witnessless.

#### 3.3.2 Cohomological reading (non-normative)
For a two-set cover `{U_a, U_b}` with overlap `U_ab`, the Čech `d⁰(s_a, s_b) = ρ_b(s_b) − ρ_a(s_a)`; `Ȟ⁰ = ker d⁰` is the space of global sections (POS locus) and the obstruction to gluing is the failure of `d⁰` to hit `0` (NEG). The fiber-product formulation above is the honest set-valued (non-abelian) statement; the `Ȟ¹` language is its abelian linearization, used only for intuition. **Compute the fiber product, not a cohomology group.**

### 3.4 Claim-variable semantics (the hard core — specify, do not hand-wave)

> **This section is the actual research-and-engineering weight of the spec.** §3.1–§3.3 are the easy topology. Extracting typed constraints from document nodes and aligning their variable namespaces across independently-authored filings is where the difficulty and the failure modes live. WO_FIBER_007 is ~the majority of real effort; scope it accordingly.

**3.4.1 Claim atoms.** An `ExtractionAdapter` maps a node `n` to a set of typed **claim atoms**:

```
Atom = ( predicate : FiboProperty | RegisteredPredicate,
         args      : [CanonicalId],        -- entities: GLEIF LEI; instruments/roles: FIBO IRI
         value     : Option<CanonicalMeasure>,   -- units/currency/date canonicalized
         polarity  : {asserted, negated},
         egrade    : EGrade )               -- confidence of THIS extraction
ClaimVar = ( predicate, arg_position ) resolved to a CanonicalId | CanonicalMeasure slot
```

Atoms are typed against the **same vocabularies used to build `E_R`** — GLEIF LEI for entity identity, FIBO for relation/role predicates, canonical measures for values. Deliberate: variable alignment across documents reuses the entity-resolution join key, not a new namespace. Two nodes share a claim-variable iff they bind the *same* `(FIBO-predicate, canonical-arg)` slot.

**3.4.2 The three helper functions, now defined.**

```
shared_claim_vars(a, b) := { v : v ∈ vars(extract(a)) ∧ v ∈ vars(extract(b)) }
                           -- intersection over the canonical (predicate, arg) namespace

restrict(n, X)           := project extract(n)'s atoms onto the slots in X,
                            = None if any atom touching X has egrade < E_floor (forced-ZERO, §3.4.3)

fiber_product(ra, rb)    := constraint join: NonEmpty(pair) if ∃ assignment satisfying
                            both restricted atom-sets on X (agree on value, compatible polarity);
                            Empty(pair) if the shared slots are bound to provably-incompatible
                            values/polarities (the disagreeing witness)
```

Value compatibility is decided by canonical-measure equality within a declared tolerance (dates to a granularity, currency after FX-normalization to a base at filing date, percentages to a bp tolerance) — all governed config, all logged into the Episode Test field.

**3.4.3 Forced-ZERO floor (ties extraction quality to abstention).** If extraction cannot produce typed atoms at or above `E_floor` for a slot in `X_ab`, `restrict` returns `None` and the verdict is `ZERO` (no-test-possible) — **never** a guessed `POS`. Low-quality extraction degrades to honest abstention, exactly as conformal descent does (§6.2). This is the semantic-layer analogue of INV-F5.

**3.4.4 Extraction is itself E-graded and flows to the verdict.** See INV-F9: a verdict's E-grade is capped by the minimum E-grade of the endpoint extractions it rests on. A POS built on E1 extractions is an E1 POS, not an E4 one.

### 3.5 Termination

- `descend` is `⊑`-monotone: strictly decreasing tree depth, well-founded on finite depth → terminates per fiber.
- `traverse` follows `E_R`, which may be cyclic ("DAG or worse") → **must** be bounded by a hop budget `H_max`. Termination of a plan holds iff traverse count `≤ H_max` (INV-F7).
- **Frontier growth is bounded separately.** Hop-count bounding does *not* bound frontier size, since `traverse` fans out (`→ 2^V`). A beam cap `K` bounds the live frontier (INV-F10); without it the anchored-fiber set can grow `b^{H_max}` (§9).

---

## 4. The retrieval algebra (IR)

A retrieval plan is a **guarded word in the free monoid on `{descend, traverse}`**. Illustrative types (agent: rebind against `BINDING.md`):

```rust
enum Verdict { Pos, Zero, Neg }

struct FiberId(/* document id d */ Uuid);
struct NodeId(Uuid);
enum EdgeClass { Containment, Relational(RelType) }

struct SectionRef(String);
struct PageAnchor { doc: FiberId, page: u32, section: SectionRef }

/// The composite graph H. Backed by hg_read_kernel; page anchors from the adapter.
trait CompositeGraph {
    fn parent(&self, n: NodeId) -> Option<NodeId>;                 // ⊑, single-parent
    fn children(&self, n: NodeId) -> Vec<NodeId>;                  // ⊑, within-fiber
    fn relational(&self, n: NodeId, r: RelType) -> Vec<NodeId>;    // E_R, many-to-many
    fn anchor(&self, n: NodeId) -> Option<PageAnchor>;             // leaf page/section
    fn fiber(&self, n: NodeId) -> FiberId;                         // π
    fn extract(&self, n: NodeId) -> Vec<Atom>;                     // §3.4 claim atoms (E-graded)
}

enum Op { Descend(Query), Traverse(RelType, Query) }
struct Plan(Vec<Op>);                       // guard lives inside Descend (§6.2)

struct ConformalCfg { alpha: f64, calib: CalibrationSetId } // coverage 1 - alpha, split-conformal
struct Budget { h_max: u32, beam_k: u32 }   // traverse hop cap (INV-F7) + frontier cap (INV-F10)

struct RetrState {
    frontier: BTreeSet<NodeId>,             // |frontier| ≤ beam_k  (INV-F10)
    ctx:      ConvCtx,                       // conversation history across turns
    evidence: Vec<Evidenced>,
    trace:    AttTrace,                      // feeds the Mellumwork Episode
}
```

### 4.1 Operational semantics

```
traverse(r, q) :  σ ↦ σ'
    frontier'  = ⋃_{v ∈ frontier} { w : (v,r,w) ∈ E_R ∧ WallGuard.visible(w, ctx) }
    frontier'' = beam_select(frontier', q, beam_k)          // INV-F10: keep top-K by relevance
    deterministic given H and the beam scorer; records one hop in trace; count ≤ h_max  (INV-F7)

descend(q)     :  for each tree-internal v ∈ frontier:
    S ← conformal_child_set(v, q, ctx, cfg)      // §6.2 split-conformal set, coverage 1−α
    if |S| = 1 : advance to the child (⊑-monotone)
    else       : freeze at v, mark that path Verdict::Zero  (abstain, §6.2, INV-F5)
    only follows E^⊑, only within fiber(v)                                     (INV-F2)
```

`descend` never crosses `E_R`; `traverse` never crosses `E^⊑`. Edge-class purity is INV-F2 and is statically checkable. `beam_select` is a **deterministic** scorer (no LLM) so `traverse` stays the cheap router; the beam is a cap, not a semantic decision.

### 4.2 AgentPlane mapping
`Op::Descend` and `Op::Traverse` are two new composition primitives over the existing AgentPlane set; the abstention guard is the **already-specified conformal abstention IR guard** from `AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC.md`, not new infrastructure. Bind, do not reimplement. **Confirm in WO_FIBER_001 that the existing guard exposes a configurable nonconformity score and a calibration-set handle (§6.2); if it hard-codes a score, that is a binding gap to surface, not to work around.**

### 4.3 Plan synthesis (who writes the guarded word)
A `Plan` is synthesized by a **planner** from the query + base-graph schema. Two supported modes, declared per deployment:
- **Policy planner** (deterministic): fixed `(traverse RelType)+ ; descend` templates keyed by query intent. No per-query LLM cost. Default for the ownership-DAG regime.
- **LLM planner**: emits the word; **its per-query cost is a real term in §9 and its output is validated** (edge-class purity, `H_max`, RelType ∈ schema) before execution. An invalid plan is rejected, not repaired silently.

---

## 5. SP-ADAPT-TREE-001 — Structural ingestion adapter

PageIndex-class parsing is an **ingestion adapter**, not an architecture. It builds the per-document containment subgraph, which the linking pass then welds into `H`.

```rust
/// One TreeAdapter per source family, under the DatasetCatalogEntry v1 adapter contract.
trait TreeAdapter {
    fn parse(&self, doc: RawDoc, policy: &WallGuard) -> Result<TreeFragment>;
}

struct TreeFragment {
    nodes:       Vec<CatalogNode>,                 // DatasetCatalogEntry-conformant
    containment: Vec<(NodeId, NodeId)>,            // E_d^⊑ (parent, child)
    anchors:     BTreeMap<NodeId, PageAnchor>,     // leaves → exact page/section
    labels:      BTreeMap<NodeId, VisibilityLabel>,// WallGuard, PER NODE (INV-F4)
    atoms:       BTreeMap<NodeId, Vec<Atom>>,      // §3.4 claim atoms, E-graded (INV-F9)
}
```

### 5.1 Adapter obligations
- **Per-node visibility.** WallGuard labels attach at ingestion, per node — a section may carry different visibility than its siblings. This is where the policy plane PageIndex entirely lacks is injected. No document is parsed that the consent lattice has not cleared.
- **Anchor totality.** Every leaf carries a `PageAnchor` (INV-F3).
- **Extraction at ingest.** Claim atoms (§3.4) are extracted per node at ingestion and stored, each carrying its own E-grade; the verdict engine reads them, it does not re-extract at query time. Extraction failure yields *no atoms* (→ forced-ZERO downstream), never fabricated atoms.
- **Schema conformance.** Nodes validate against `DatasetCatalogEntry v1`; the adapter is registered like any other high-priority source adapter (GLEIF-LEI, FIBO, eCFR/Federal Register, OpenSky).

### 5.2 Cross-linking pass (trees → `E_R`)
After tree construction, a linking pass writes `E_R` edges between nodes in **different** fibers:
- **Join key:** GLEIF LEI (entity identity).
- **Relation vocabulary:** FIBO.
- **Precision is measured, not assumed.** The linker emits a per-edge match confidence; `E_R` precision `P_R` is a reported metric (§7 WO_ADAPT_004) because both cost and recall depend on it (§9). Low-confidence links are graded, not silently trusted.
- **Worked target:** the Nasdaq ownership DAG — nodes anchored in filing trees, edges = GLEIF Level-2 relationship records. The edge `⟨entity@§4.2 of filing A⟩ —owns→ ⟨entity@§2.1 of filing B⟩` is inexpressible in either `T_A` or `T_B` alone and is exactly an `E_R` edge whose endpoints remain anchor-reachable through their fibers.

---

## 6. Verdict + attestation engine

### 6.1 Fiber-product verdict (implements §3.3, §3.4)

```rust
fn glue_verdict(e: RelEdge, g: &impl CompositeGraph) -> (Verdict, Option<Witness>, EGrade) {
    let overlap = shared_claim_vars(e.a, e.b, g);
    if overlap.is_empty() { return (Verdict::Zero, None, EGrade::NA); }        // vacuous cover
    let (ra, rb) = (restrict(e.a, &overlap, g), restrict(e.b, &overlap, g));   // §3.4.2/§3.4.3
    match (ra, rb) {
        (None, _) | (_, None) => (Verdict::Zero, None, EGrade::NA),            // forced-ZERO floor
        (Some(ra), Some(rb)) => {
            let eg = min_egrade(&ra, &rb);                                     // INV-F9
            match fiber_product(ra, rb) {
                FP::NonEmpty(agree)  => (Verdict::Pos, Some(Witness::Agree(agree)), eg),
                FP::Empty(disagree)  => (Verdict::Neg, Some(Witness::Disagree(disagree)), eg),
            }
        }
    }
}
```

### 6.2 Conformal abstention (implements INV-F5) — an earned guarantee

The v0.1.0 "coverage 1−α" was a label. It is now split-conformal with a stated guarantee.

- **Nonconformity score.** At node `v` with children `c_1…c_k`, a base scorer `s(v, c_i, q)` (LLM logit or reranker score) is turned into an **adaptive prediction set (APS)** nonconformity score: `A(v, c, q) = Σ_{c' : s(c') ≥ s(c)} softmax(s)_{c'}` (cumulative mass down to the true child). APS is used, not naive thresholding, so set size adapts to node difficulty.
- **Calibration set.** A held-out `CalibrationSetId` of `(v, q, correct_child)` triples drawn from the corpus. Split-conformal quantile `q̂ = ⌈(n+1)(1−α)⌉/n` of the calibration nonconformity scores defines the set: `S = { c : A(v,c,q) ≤ q̂ }`. Guarantee: `P(correct_child ∈ S) ≥ 1−α`, **marginal over the calibration distribution.**
- **Exchangeability, honestly.** Trees are *not* exchangeable, so calibration is over the **scorer's residuals**, not over node identities — the score function is tree-agnostic, which is the defensible exchangeability level. To recover approximate *conditional* coverage, calibration is **Mondrian / group-conditional**: stratified by `(branching-factor bucket, depth bucket, source-family)`, with a per-group quantile. This directly answers "every ToC is its own distribution."
- **Shift ⇒ recalibrate.** Coverage holds only on-distribution. A new `source-family` with no calibration stratum is `E1` for descent and **must** recalibrate before its coverage claim is graded above E1 (ties to §0.5 rule 5 and INV-F9).
- **Semantics.** Singleton `S` → advance; non-singleton → `ZERO` on that path. Converts PageIndex's worst failure mode (confident descent down the wrong branch → hallucinated citation) into a principled `ZERO` rather than a wrong `POS`.

### 6.3 Double grounding
Every returned edge carries **both** provenances:
- *provenance-of-location*: the `PageAnchor` at each endpoint's fiber leaf;
- *provenance-of-claim*: the `Verdict` + E-grade from §6.1.

**Interaction with abstention (INV-F3 × INV-F5).** A multi-hop answer requires *both* endpoints anchored to leaves (INV-F3) *and* a non-ZERO verdict. If conformal descent abstains before reaching a leaf, the endpoint is unanchored, the edge cannot be doubly grounded, and the whole path returns `ZERO` — correctly, but this means **abstention rate is a first-class quality metric, not a side effect** (§7 WO_FIBER_008). A system that is "never wrong" by being "usually ZERO" is a failure, and the eval must expose it.

### 6.4 Mellumwork Episode assembly (STOPGATE-emitted)
Bind the composite result into one Episode:

```
Artifact     = source page(s)          (tree leaf/leaves; PageAnchor)
Claim        = the relational edge       (E_R)
Test         = cross-fiber fiber-product consistency (§3.3/§3.4), incl. tolerance config used
Attestation  = hash-chained Episode, harness-emitted, model removed from critical path (STOPGATE)
Narrative    = answer carrying BOTH citation types + verdict E-grade
```

A returned Narrative with no Episode is a failed path (§0.5 rule 4).

---

## 7. Work orders

| WO | Title | Depends | Acceptance |
|---|---|---|---|
| `WO_FIBER_001` | **Repo binding.** Read `hg_read_kernel`, `DatasetCatalogEntry v1`, `WallGuard`, `Mellumwork`, AgentPlane primitives; emit `BINDING.md` + `SP_RETR_FIBER_001_axis_binding.md` mapping every §3.4/§4/§5 symbol to real types. Confirm the AgentPlane conformal guard exposes a configurable score + calibration handle (§4.2). | — | `BINDING.md` covers 100% of spec symbols; axis-binding ratified; CI asserts no later WO imports from this spec's pseudocode. |
| `WO_FIBER_002` | **Composite graph schema.** Add `EdgeClass` to hellgraph nodes/edges; enforce `E^⊑ ⊔ E_R` disjointness + single-parent containment; migration. | 001 | INV-F1, INV-F2 property tests green. |
| `WO_ADAPT_003` | **TreeAdapter + parser + extraction.** PageIndex-class structural parse → `TreeFragment`; per-node WallGuard labeling; anchor totality; §3.4 atom extraction with per-atom E-grade. | 002 | INV-F3, INV-F4, INV-F9 (extraction path) green; validates against `DatasetCatalogEntry v1`. |
| `WO_ADAPT_004` | **Cross-linking pass.** GLEIF-keyed entity resolution → `E_R`; FIBO relation binding; **per-edge `P_R` reported**; Nasdaq ownership subgraph fixture. | 003 | Ownership DAG fixture reconstructs a known Level-2 chain; endpoints anchor-reachable; `P_R` computed on fixture. |
| `WO_FIBER_005` | **Retrieval IR + planner.** `Op`/`Plan`/`RetrState`; `descend`/`traverse` wired to AgentPlane primitives; `H_max` + `beam_k`; plan-validation (§4.3). | 002 | INV-F2, INV-F7, INV-F10 green; edge-class purity static check; invalid plans rejected. |
| `WO_FIBER_006` | **Abstention guard.** APS nonconformity score + split-conformal + Mondrian strata (§6.2); ZERO on non-singleton. | 005 | INV-F5 green; **empirical coverage on held-out ≥ 1−α per stratum**; injected-ambiguity probe yields ZERO not wrong POS. |
| `WO_FIBER_007` | **Verdict + Episode engine.** `shared_claim_vars`/`restrict`/`fiber_product` (§3.4); forced-ZERO floor; STOPGATE Episode; double grounding; E-grade propagation. | 004, 006 | INV-F6, INV-F8, INV-F9 green; every POS/NEG carries a witness; low-extraction slots yield ZERO not POS. |
| `WO_FIBER_008` | **Conformance + eval + gate.** Single-doc (FinanceBench-class) **and** multi-hop ownership-DAG evals; **report accuracy, abstention rate, empirical coverage, and `P_R`-sensitivity per condition**; E-grade gate; Michael-only promotion. | 007 | All INV green; evals report per-condition incl. abstention rate; promotion blocked below E4 without Michael sign-off. |

---

## 8. Invariants (machine-checkable)

- **INV-F1 (containment integrity).** `E^⊑` is a forest; every node has ≤ 1 containment parent.
- **INV-F2 (edge-class purity).** `descend` follows only `E^⊑` within one fiber; `traverse` follows only `E_R`. No op mixes classes. *Static.*
- **INV-F3 (anchor totality).** Every leaf carries a `PageAnchor`; every `E_R` endpoint is anchor-reachable. *(See INV-F5 interaction: an unanchored endpoint ⇒ ZERO, never a fabricated anchor.)*
- **INV-F4 (policy precedence).** No node enters a frontier unless `WallGuard.visible` under `ctx`; retrieval visibility ⊆ ingestion labels.
- **INV-F5 (abstention soundness).** `descend` advances only on a singleton split-conformal set whose empirical coverage on the matching stratum is ≥ `1−α`; else `ZERO`. No guessed child ever advances. *Coverage claim void off-distribution (§6.2).*
- **INV-F6 (verdict faithfulness).** Edge verdict = fiber-product status (§3.3/§3.4). `POS` ⟹ agreeing witness; `NEG` ⟹ disagreeing witness. Only `ZERO` may be witnessless.
- **INV-F7 (hop boundedness).** `traverse` count ≤ `H_max` per plan ⟹ termination over cyclic `E_R`.
- **INV-F8 (attestation completeness).** Every returned Narrative binds provenance-of-location **and** provenance-of-claim in one hash-chained Mellumwork Episode.
- **INV-F9 (extraction/verdict E-grade monotonicity).** A verdict's E-grade ≤ min E-grade of the endpoint extractions it rests on; a slot below `E_floor` forces `ZERO` (§3.4.3). No verdict is graded above the evidence under it.
- **INV-F10 (frontier boundedness).** `|frontier| ≤ beam_k` at all times; `beam_select` is deterministic. Bounds anchored-fiber count against `traverse` fan-out (§9).

---

## 9. Cost model

Let `b` = max relational fan-out per `traverse`, `K` = `beam_k`, `H` = `H_max`, `P_R` = `E_R` linker precision.

**Per query:**
```
LLM calls =  C_plan                                   -- plan synthesis (0 if policy planner; §4.3)
          +  Σ_{d ∈ anchored} O( depth(T_d) · branch )   -- fine descent, LLM
   where |anchored| ≤ min( K·H , b^{H} )   -- frontier is beam-capped (INV-F10), else exponential

Deterministic (non-LLM) =  O( H · b )  traverse expansions  +  O(K·H · log b)  beam scoring
depth(T_d) ~ log|d|   for a balanced ToC
```

**Corrections vs v0.1.0:**
1. **Frontier is not free.** `Σ_{d ∈ anchored}` is the dominant LLM term, and without the beam cap `|anchored|` grows `b^{H}`. The `K` cap (INV-F10) is what makes the "strictly better" claim true; it is a *design commitment*, not incidental. State `K` and `H` as governed config.
2. **Plan synthesis has a cost.** `C_plan` is zero only under the policy planner. An LLM planner adds a real per-query LLM term that the v0.1.0 model omitted.
3. **The advantage is conditional on `P_R`.** The cost win rests on `traverse` narrowing to the *right* fibers. Under-linking (`P_R` low) → the right fiber is missing → confident `ZERO` (recall loss disguised as abstention). Over-linking → the descent blowup you escaped returns. So the "strictly better point on the curve" holds **for high-`P_R` `E_R` in the multi-hop-plus-exact-citation regime** — WO_FIBER_008 reports `P_R`-sensitivity precisely because the claim is conditional on it.

Net: still a strictly better point than pure PageIndex over a synthetic-root forest walk (which pays LLM descent over *everything*), **provided** `K`-beam is enforced and `P_R` is high. Both are now measured, not assumed.

---

## 10. Open binding points (agent: resolve in WO_FIBER_001)

1. `hg_read_kernel` — exact signature for typed relational adjacency and whether `EdgeClass` is a first-class edge attribute or a separate relation namespace. Bind `CompositeGraph` incl. `extract`.
2. `DatasetCatalogEntry v1` — the node schema fields holding `PageAnchor`, per-node `VisibilityLabel`, and the per-node `Atom` list with E-grades. **Confirm the type even exists under this name** (did not grep-match in-estate on authoring) and its adapter-registration path.
3. `Mellumwork` Episode schema — exact Artifact/Claim/Test/Attestation/Narrative field names and the hash-chain succession contract. Bind §6.4. Confirm where the verdict E-grade lives.
4. AgentPlane — the primitive-registration surface for `Descend`/`Traverse`, and whether the existing conformal-abstention guard exposes a **configurable nonconformity score + calibration-set handle** (§4.2/§6.2). If it hard-codes a score, surface as a gap.
5. `WallGuard` — visibility predicate signature and whether labels are lattice-valued (confirm `VisibilityLabel` type).
6. GLEIF/FIBO — confirm the canonical-measure normalization utilities (FX-at-date, date granularity, bp tolerance) exist or must be built for §3.4.2 value compatibility.
7. Choose defaults, expose as governed config: `α` (conformal coverage), `H_max` (hops), `beam_k` (frontier cap), `E_floor` (extraction floor), value tolerances.

---

*Authored at E1 from estate memory, not a fresh repo read. Every interface reference is a binding point, not a claim about current code. Promotion past E1 requires WO_FIBER_001 to reconcile these against live repo reads. v0.2.0 closed the five v0.1.0 review holes (sheaf-is-notation, claim-variable semantics, real conformal calibration, corrected cost model, abstention-rate eval); it did **not** add repo-grounding — that is still WO_FIBER_001's job.*
