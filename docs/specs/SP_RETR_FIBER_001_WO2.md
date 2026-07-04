# SP-RETR-FIBER-001 — WO_FIBER_002 (composite-graph schema)

**Work order:** `WO_FIBER_002` — composite graph schema (`E^⊑ ⊔ E_R`) + Crystal Atlas→hellgraph projection + relation index
**Depends on:** `WO_FIBER_001` (`SP_RETR_FIBER_001_BINDING.md`) merged. **This doc imports symbols from BINDING.md, not from the spec pseudocode.**
**Status:** DESIGN (ready to apply); the hellgraph edit is **coordination-gated** — see §0.
**Decisions applied (BINDING.md §5):** substrate = hellgraph runtime + Atlas projected; `EdgeClass` = **first-class atom field**; adapter = fixtures-first.

---

## 0. Coordination gate (read first — this WO touches a hot repo)

WO_FIBER_002 modifies **`~/dev/hellgraph`** (`hg_core` schema + migration + `hg_read_kernel`). That repo is under active concurrent hardening by another agent (security "annealing epochs", 0.4.x releases, 2026-07-04). Two conditions **must** hold before the hellgraph edit lands:

1. **PR #316 merged** (spec §0.5.2: one WO, one PR; do not open N+1 until N merges).
2. **A clean window on hellgraph** — fetch `origin/main`, confirm no in-flight schema churn, branch off a current `main`, and flag the schema change to the owner. Never rebase over or collide with the other agent's branches. If HEAD has flipped or a conflicting schema edit is in flight, STOP and surface.

Everything in this doc up to §1 is design and lives in agentplane (in-lane). The `hg_*` crate edits in §2–§3 are the only hellgraph-touching part and are what the gate protects.

---

## 1. What WO_FIBER_002 delivers

1. `LinkAtom.edge_class: EdgeClass` — a first-class field on hellgraph edges.
2. A migration defaulting all existing links to `Relational` (no existing edge is containment).
3. Class-filtered adjacency in `hg_read_kernel` + a **relation index** (fixes the O(|atoms|) scan `incident_links` does today, `hg_read_kernel/src/lib.rs:79`).
4. `ι_d`: the Crystal Atlas → hellgraph projection with a string↔`u128` id-map.
5. Property tests for INV-F1 (containment forest) and INV-F2 (edge-class purity, now static).

---

## 2. hellgraph schema change (`hg_core`) — coordination-gated

```rust
// hg_core/src/lib.rs — new, additive
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EdgeClass {
    Containment,   // E^⊑ — single-parent, per-fiber, mereological
    Relational,    // E_R — typed many-to-many (default for all pre-migration links)
}

// LinkAtom (currently lib.rs:206) gains one field:
pub struct LinkAtom {
    pub hdr: AtomHeader,
    pub semantics: LinkSemantics,
    pub members: Vec<RoleBinding>,
    pub edge_class: EdgeClass,   // NEW
}
```

**Migration.** Every persisted `LinkAtom` without `edge_class` deserializes to `EdgeClass::Relational` (serde `#[serde(default = "…relational")]` or an explicit migration pass over the journal). Rationale: containment edges only ever originate from the `TreeAdapter` (§WO_ADAPT_003), so no pre-existing edge is containment.

**INV-F1 enforcement (containment integrity).** A write-side check: for any `LinkAtom` with `edge_class == Containment`, its `members` must encode exactly one `parent` role and one `child` role, and no atom may be the `child` of two distinct containment links (single-parent forest). This is a new invariant on the write kernel (`hg_kernel`), asserted in the migration and on insert.

**INV-F2 enforcement (edge-class purity) — now static.** Because `edge_class` is a typed field, `descend` filters `edge_class == Containment` and `traverse` filters `edge_class == Relational` at the type level; a mixed walk is unrepresentable. This is the payoff of the first-class-field decision over the reserved-`type_name` alternative.

---

## 3. Read-side: class-filtered adjacency + relation index (`hg_read_kernel`)

```rust
// additive to hg_read_kernel/src/lib.rs
pub fn incident_links_of_class<S: ReadKernelStore>(
    store: &S,
    subject_atom: AtomId,
    class: EdgeClass,
) -> Vec<IncidentLinkSummary>;   // incident_links(...) filtered by edge_class
```

**Relation index (fixes the scan).** `incident_links` today is `store.all_atoms().filter(...)` — O(|atoms|) per hop (`lib.rs:79-101`). At `beam_k=8`, `H_max=4` that is up to 32 full-graph scans per query. WO_FIBER_002 adds an adjacency index maintained on write:

```
index: Map<(AtomId /*target*/, EdgeClass), Vec<AtomId /*link_atom*/>>
```

built in `hg_kernel` alongside the atom store, so `incident_links_of_class` is O(deg) not O(|atoms|). Without this, §9's cost model is understated and INV-F10's beam cap doesn't save the adjacency cost. **This index is a prerequisite for the cost claim, not an optimization.**

---

## 4. `ι_d` — Crystal Atlas → hellgraph projection (in-lane; prophet-platform + agentplane)

Maps the ingestion/evidence contracts (string ids) into hellgraph atoms (`u128`):

| Crystal Atlas (source) | hellgraph (target) |
|---|---|
| `graph-node.v0.node_id: string` | `NodeAtom` with fresh `AtomId: u128`; id-map row `(node_id ↔ atom_id)` |
| `graph-node.v0.attributes` | `ValueEnvelope{ key: Prop("attr:<k>"), … }` per attribute |
| `evidence.v0.anchor_ref` (+ `source_ref`, `confidence`) | `ValueEnvelope{ key: Prop("anchor"), payload: anchor_ref, epistemic_mode: derived }` — this is `PageAnchor` (INV-F3) |
| containment edge (from `TreeAdapter`) | `LinkAtom{ edge_class: Containment, members: [parent, child] }` |
| GLEIF Level-2 cross-link | `LinkAtom{ edge_class: Relational, type_name: <FIBO prop>, members: […] }` |
| `confidentiality_class` (WallGuard) | `ValueEnvelope.security: SecurityLabel` (INV-F4 visibility) |
| `distribution_class` (Atlas) | separate axis — **not** retrieval visibility; carried for `SP-EXPORT-LD-001` only |

**Id-map** `(tenant_id, node_id) ↔ AtomId` is authoritative and persisted; `ι_d` is idempotent (re-ingest updates values, does not mint new atoms for an existing `node_id`).

---

## 5. Acceptance (spec §7 WO_FIBER_002 row)
- INV-F1 property test: random tree fragments → containment links form a single-parent forest; a double-parent insert is rejected.
- INV-F2 static test: a walk cannot mix classes (type-level); `descend`/`traverse` compile only against their class.
- Relation-index test: `incident_links_of_class` returns the same set as the filtered scan, at O(deg).
- `ι_d` round-trip: a Crystal Atlas fixture (`graph-node.v0` + `evidence.v0`) projects to atoms and the `anchor_ref` is recoverable as `PageAnchor`; re-ingest is idempotent (no atom duplication).

---

## 6. Premium tier note (deferred, not in WO series)
The **Atlas-native substrate** (H living in `graph-node.v0`/`graph-edge.v0` with hellgraph as one federated backend) is retained as a **second premium managed/hosted offering**. It is not built by WO_FIBER_002–008; the base path is hellgraph-runtime. Tracked separately so the fibered retrieval work does not fork on it.

---

*Design ready. The `hg_core`/`hg_kernel`/`hg_read_kernel` edits (§2–§3) are the only hellgraph-touching part and are held behind the §0 coordination gate. §4's projection + all tests are in-lane and can proceed first.*
