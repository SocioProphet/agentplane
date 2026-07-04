# SP-RETR-FIBER-001 — BINDING.md (WO_FIBER_001)

**Work order:** `WO_FIBER_001` (repo binding — the mandatory bind-before-build gate, spec §0.5.1)
**Status:** COMPLETE (reconnaissance) / DRAFT (mappings pending review)
**Method:** read-only reconnaissance of live repos on 2026-07-04. Five parallel probes; the load-bearing signatures (`conformal_gate`, `hg_read_kernel`, `narration_fidelity_verifier` verdicts, Crystal Atlas `evidence.v0`/`graph-node.v0`) were **re-read directly** by the author, not relayed. Everything below is a real `file:line`, or is marked **ABSENT → BUILD**.
**Rule enforced:** every later WO imports symbols from *this* file, never from the spec's illustrative Rust (spec §0.5.1).

---

## 0. Headline: the spec assumed one substrate; there are two

`H` does not live in a single graph. It spans a **two-layer stack**, and this is the most important thing WO_FIBER_001 found:

| Layer | Repo | Identity | Role for `H` |
|---|---|---|---|
| **Relational engine** | `~/dev/hellgraph` (Rust) | `AtomId = u128` | The runtime graph: atoms + links, typed adjacency, versioned values. Where `descend`/`traverse` execute. |
| **Catalog / evidence contracts** | `~/dev/prophet-platform` Crystal Atlas (JSON schema) | `node_id: string` | The ingestion + provenance schema: `asset-catalog-entry.v0`, `evidence.v0` (holds the page anchor), `graph-node.v0`/`graph-edge.v0`. What `TreeAdapter` emits. |
| **Policy plane** | `~/dev/policy-fabric` (+ `agentplane/tools`) | record dicts | WallGuard access evaluation + confidentiality lattice. |
| **Attestation + guards** | `~/dev/agentplane` (Python) | sha256 content-addr | Verdict enum, conformal gate, StopGate artifacts, Mellumwork tiers. |

**Consequence for the model (spec §3.1).** The injection `ι_d : V_d ↪ V` is not a nicety — it is a **real cross-layer projection** from Crystal Atlas records (string `node_id`, carrying `anchor_ref`) into hellgraph atoms (`u128 AtomId`). WO_FIBER_002 must own this projection and the id-mapping table. The spec's implicit "one graph" framing is wrong; keep the two layers distinct and bridge them explicitly.

---

## 1. Symbol binding table (spec §3.4/§4/§5 → real types)

| Spec symbol | Real binding | `file:line` | Note |
|---|---|---|---|
| `NodeId` (`Uuid`) | `hg_core::AtomId = u128` | `hellgraph/crates/hg_core/src/lib.rs:3` | **Spec type is wrong** — not UUID. `u128`, assigned at creation, not content-hashed. |
| node / edge atoms | `Atom::{Node,Link}`; `NodeAtom{hdr}`, `LinkAtom{hdr,semantics,members}` | `hg_core/src/lib.rs:171,194,206` | Nodes + edges are both `Atom`s; `AtomKind{Node,Link}` at `:171`. |
| `RelType` | `LinkAtom.hdr.type_name: String` (+ `LinkSemantics`) | `hg_core/src/lib.rs:177,186` | Relation type is a free string on the link header; `LinkSemantics{DirectedBinary,OrderedNary,UnorderedNary,SetLike,MultiSetLike}`. |
| `EdgeClass{Containment,Relational}` | **ABSENT → BUILD** | — | hellgraph has **no** containment-vs-relational distinction. WO_FIBER_002 must introduce it — cleanest as a **reserved `type_name` namespace** (e.g. `⊑`-prefixed) rather than a new atom field, to avoid a schema migration. This is real work, not a flag. |
| `CompositeGraph::relational(n,r)` | `hg_read_kernel::incident_links(store, n)` filtered by `link_type == r` | `hellgraph/crates/hg_read_kernel/src/lib.rs:75` ✅verified | Returns `Vec<IncidentLinkSummary{link_atom,link_type,semantics,roles}>` (`:5`). **Unindexed full-atom scan** (`:79-101`) — see cost note §4. |
| `CompositeGraph::{parent,children}` (`E^⊑`) | `incident_links` filtered by the reserved containment `type_name` | `.../lib.rs:75` | Once `EdgeClass` exists (above), containment walk is the same read, filtered to the `⊑` namespace. |
| `CompositeGraph::anchor(n) → PageAnchor` | `evidence.v0.anchor_ref: string` | `prophet-platform/contracts/crystal-atlas/schemas/evidence.v0.schema.json` ✅verified | Anchor is a **string** on the evidence record (catalog layer), not a `{doc,page,section}` struct. Bind `PageAnchor` = `evidence.v0` (`anchor_ref` + `source_ref` + `confidence`). |
| store handle | `trait ReadKernelStore` (impls: `SpaceStore`, `JournaledStore`) | `.../hg_read_kernel/src/lib.rs:23,31,53` ✅verified | 5 methods: `atom_by_id`, `all_values`, `all_atoms`, `read_field_at`, `read_proof_at`. |
| node properties / claim `Atom`s (§3.4) | `ValueEnvelope{subject_atom,key,payload,epistemic_mode,security}`, `ValueKey::Prop(String)` | `hg_core/src/lib.rs:147,160` | Per-node typed attributes are versioned value envelopes keyed by `Prop("...")`. Claim atoms live here. |
| `Atom.egrade` (extraction confidence) | `evidence.v0.confidence: number` at ingest; `ValueEnvelope.epistemic_mode` at rest | evidence.v0 (verified); `hg_core/src/lib.rs:160` | See axis-binding: this is the **provenance/evidence axis**, not a numeric `E0..E5`. |
| `VisibilityLabel` / `WallGuard.visible` | `wallguard_policy_evaluator.evaluate(record) → dict{decision.outcome}` | `policy-fabric/tools/wallguard_policy_evaluator.py:46` | **No `visible()->bool`.** Bind: *visible* ⟺ `outcome ∈ {allow, clean_room_release_allowed}`; everything else (`deny/redact/quarantine/escalate`) is **not-visible, fail-closed**. |
| `VisibilityLabel` type | `confidentiality_class` enum (lattice) | `policy-fabric/contracts/wallguard-policy-decision.v0.schema.json` | `{public, firm_approved, client_confidential, matter_restricted, wall_restricted, clean_room_derived}`. Mount the partial order on the reusable `agentplane/tools/taint_lattice.py:43 class Lattice{leq,join,meet}`. |
| `Verdict{Pos,Zero,Neg}` | `narration_fidelity_verifier`: `POS, ZERO, NEG, INDETERMINATE` | `agentplane/tools/narration_fidelity_verifier.py:33` ✅verified | Real enum has a **4th value** `INDETERMINATE`. Mapping in §2. `_VERDICT_TO_FINDING={POS:"OK",NEG:"VIOLATION",ZERO:None,INDETERMINATE:None}` (`:36`). |
| conformal abstention guard | `conformal_gate.CalibratedGate.classify(score)->ACCEPT|INDETERMINATE`; `calibrate(scores,correct,alpha)` | `agentplane/tools/conformal_gate.py:47,56,71` ✅verified | **Configurable** via `verifier-ir.schema.v0.2.json:37` (`alpha`,`calibration_set_id`,`score_fn_id`). Binding requirement (spec §4.2) **SATISFIED — no gap.** But it is **CRC, not APS** — see §2. |
| Mellumwork Episode (5-field) | **ABSENT → BUILD on StopGate.** Mellumwork = T1/T2 tiers only | `agentplane/tools/mellumwork.py:1,25` | `mellumwork.py` is a **tiering framework** (`T1`=proof/permit-eligible, `T2`=test), not an Episode schema. The 5-field Episode exists only in the spec. Emit it as a **StopGate artifact body**. |
| Episode attestation / hash-chain | `stopgate_artifact.sign_artifact()` (ed25519), `artifact_id()`=sha256, chain via `override_of` | `agentplane/tools/stopgate_artifact.py:314,409,397,145` | `signature={alg:"ed25519",key_id,value}`; predecessor link is the `override_of` content-address field. |
| `EGrade{E0..E5}` | **ABSENT → REBIND** to `{exact, sampled, verified}` | `agentplane/tools/mellumwork.py:25` | Numeric E-grades do not exist in code. See axis-binding + §2. |
| adapter contract `DatasetCatalogEntry v1` | `asset-catalog-entry.v0` (ingest) + `source-catalog-entry.v0` (provider) | `prophet-platform/contracts/crystal-atlas/schemas/*.v0.schema.json` | **Fictional name confirmed absent.** Rebind to Crystal Atlas. |
| `TreeAdapter` registration / source adapters (GLEIF, FIBO, eCFR…) | **ABSENT → BUILD.** Catalog Gateway is pre-MVP | `prophet-platform/docs/strategy/PROPHET_DATA_CATALOG_DESIGN.md` (§6.2) | No source-adapter registry exists; `source_kind` is a fixed enum. GLEIF/FIBO/eCFR/OpenSky are **not registered adapters in prophet-platform** (they live in `ontogenesis`/`gaia-world-model`). SP-ADAPT-TREE-001's "registered like any other source adapter" is aspirational. |
| composition-primitive registry (`Op::{Descend,Traverse}`) | **ABSENT → BUILD** (per-primitive module + IR schema + spec-§, no central enum) | pattern: `conformal_gate.py`, `step_gate.py`, `receipt_fold.py`, `taint_lattice.py`, `shape_constraints.py` | Register `Descend`/`Traverse` as new IR schema + module, mirroring `step_gate` + `stepgate-artifact.schema`. |
| IR guard mechanism | VerifierIR `finding ∈ {OK,VIOLATION,REVIEW,null}` + `evidence_refs: [sha256]`; harness-owned `g_H(e)` | `agentplane/schemas/verifier-ir.schema.v0.1.json:7` | Guards are harness-evaluated findings, not a separate type. |

---

## 2. Reconciliation findings (spec claims that reality corrected)

1. **`NodeId` is `u128`, not `Uuid`.** Mechanical but pervasive; every IR type carrying a node id rebinds.
2. **`EdgeClass` does not exist.** The vertical/horizontal edge split — the spec's whole premise — is *not* in hellgraph today. WO_FIBER_002 introduces it via reserved `type_name` namespace. The spec is a proposal to hellgraph's schema, not a description of it.
3. **The conformal guard is CRC, not APS/prediction-sets, and Mondrian is not in v0.1.** Spec §6.2 must be rewritten:
   - Real object: a **scalar threshold `λ̂`** on a monotone nonconformity score, controlling the *marginal* `P(accept ∧ wrong) ≤ α` (`conformal_gate.py:19-27`). Not a prediction set; there is no "singleton set" test.
   - **Rebind descend-abstention:** the child-selection score `s(v,c,q)` (HIGH = more likely wrong) feeds `classify()`; `ACCEPT` → advance to the argmin-score child, `INDETERMINATE` → abstain (→ ZERO per §2.4). INV-F5 rewrites to "advance only on `classify()==ACCEPT`."
   - **Mondrian → multiple `calibration_set_id`s.** Group-conditional coverage is achievable *without* new code: register one calibration set per `(branching-bucket, depth-bucket, source-family)` stratum and select `calibration_set_id` per node. This is the honest binding of my Mondrian ask onto v0.1.
   - **Small-stratum honesty is already built in:** `alpha_feasible=false` when `α < 1/(n+1)` → abstain-all (`conformal_gate.py:53,110`). That *is* the "thin stratum abstains rather than fakes coverage" behavior INV-F5 wanted.
   - **Multi-hop composition:** anytime-valid + `pasc_joint` are **deferred to v0.2** in-repo; today bind the plan-level budget to `composition_rule="bonferroni"` (conservative). Update §9/§6.2 accordingly.
4. **Mellumwork is not an Episode schema.** It is T1/T2 tiering. The 5-field Episode is a build target on top of the real **StopGate artifact** (`sign_artifact`/`artifact_id`/`override_of`). §6.4 rebinds to "assemble a StopGate artifact whose body carries {Artifact,Claim,Test,Attestation,Narrative}."
5. **E-grades are `{exact,sampled,verified}`, not `E0..E5`.** The `E1`/`E4` language in the spec must rebind to the evidence axis (see axis-binding). "E4 = Michael-only promotion" maps to the **`verified`-promotion gate** (`verified` requires durable proof material — `policy_attestation_v1.md:47`), which is the existing Michael-gated lane.
6. **Two visibility vocabularies, do not conflate.** `confidentiality_class` (WallGuard/policy-fabric — *who may see it*, access/consent) is the INV-F4 binding. `distribution_class` (Crystal Atlas `graph-node.v0`/`evidence.v0` — *how widely it may be redistributed*, licensing/packaging) is a **parallel axis**, not the same thing. INV-F4 binds to WallGuard `confidentiality_class`; `distribution_class` is a separate downstream concern (relevant to `SP-EXPORT-LD-001`, not to retrieval visibility).
7. **Source-adapter registry is pre-MVP.** SP-ADAPT-TREE-001's registration story is aspirational; the Catalog Gateway is designed but unbuilt. GLEIF/FIBO/eCFR live in other repos. WO_ADAPT_003/004 must either build the adapter path or scope the worked example to fixtures.
8. **No traversal/query surface exists** and `incident_links` is an unindexed scan. `descend`/`traverse` are net-new, and the §9 cost model must account for the O(|atoms|) adjacency read until an index exists (WO_FIBER_002 should add a relation index or the beam cost is understated).

**Verdict-value mapping (spec ZERO overloaded → real 4-value enum):**

| Spec cause | Real value |
|---|---|
| vacuous cover (`X_ab=∅`) / missing evidence / forced-ZERO floor | `ZERO` |
| conformal descent abstained | `INDETERMINATE` (guard's own output; `=None` finding, same permit consequence as ZERO) |
| fiber product non-empty | `POS` (→ finding `OK`) |
| fiber product empty, overlap ≠ ∅ | `NEG` (→ finding `VIOLATION`) |

Both `ZERO` and `INDETERMINATE` yield a null finding (no permit) — so the spec's "witnessless ZERO" invariant (INV-F6) holds for both; keep them distinct in the trace for diagnosis (why did we not answer: no-test vs abstained).

---

## 3. Config defaults resolved (spec §10.7)

| Knob | Default | Source of default |
|---|---|---|
| `alpha` (risk budget) | `0.10` | matches `test_conformal_gate.py` convention; governed. |
| `composition_rule` | `bonferroni` | only conservative option shipped in v0.1 (`conformal_gate.composition_note`). |
| `H_max` (hops) | `4` | ownership-DAG regime; governed. |
| `beam_k` (frontier cap, INV-F10) | `8` | governed; required because `incident_links` fans out with no index. |
| `E_floor` (extraction floor) | `sampled` (i.e. reject below `sampled`/`T2`) | evidence axis; `verified` for permit-eligible answers. |

---

## 4. Per-WO impact of the bindings

- **WO_FIBER_002** grows: not just add `EdgeClass`, but own the **Crystal Atlas → hellgraph projection** (`ι_d`, string→`u128` id map) **and** add a relation index so `traverse` isn't an O(|atoms|) scan.
- **WO_ADAPT_003/004**: emit `asset-catalog-entry.v0` + `evidence.v0` (anchor in `anchor_ref`); source-adapter registration is **build-or-fixture** (Gateway pre-MVP). Worked GLEIF example runs on fixtures until the Gateway exists.
- **WO_FIBER_006** simplifies: the conformal gate already exists — this WO is (a) define the child-selection `score_fn_id`, (b) build per-stratum calibration sets, (c) wire `classify()`. Not new conformal infrastructure.
- **WO_FIBER_007**: build the Episode as a StopGate artifact body; verdict via the existing `POS/ZERO/NEG/INDETERMINATE` enum + `_VERDICT_TO_FINDING`.
- **WO_FIBER_008**: E-grade gate = the `verified`-promotion gate; "Michael-only E4" = the durable-proof-material promotion lane.

---

## 5. Open decisions for the user (genuine forks, not defaults)

1. **Substrate of record for `H`.** Confirm: hellgraph atoms are the runtime graph, Crystal Atlas contracts are the ingestion/evidence schema projected into it? Or should `H` live entirely in Crystal Atlas `graph-node.v0`/`graph-edge.v0` (string ids, JSON) and treat hellgraph as one federated backend? This changes WO_FIBER_002 substantially.
2. **`EdgeClass` mechanism.** Reserved `type_name` namespace (no migration, my recommendation) vs a first-class atom field (cleaner, but a hellgraph schema change in a repo the other agent is actively hardening).
3. **Adapter path now or fixtures-first.** Build the Catalog Gateway source-adapter registration (larger), or scope SP-ADAPT-TREE-001's worked example to fixtures until the Gateway lands (faster, keeps this in-lane)?

---

*WO_FIBER_001 complete. This file — not the spec pseudocode — is the import surface for WO_FIBER_002+. The spec (`SP_RETR_FIBER_001_SPEC.md`) remains at E1 as a design narrative; where it and this file disagree, this file wins (it is repo-grounded; the spec was memory-grounded). Companion: `SP_RETR_FIBER_001_axis_binding.md`.*
