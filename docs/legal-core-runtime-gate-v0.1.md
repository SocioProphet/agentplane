# Legal Core Runtime Gate v0.1

AgentPlane is the runtime and action-admission plane for the Legal Core / World Evidence Fabric architecture.

The runtime gate exists so an agent workflow cannot convert source ingestion, document triage, endpoint investigation, world-modeling, or supply-chain enrichment into an unsafe or unscoped action.

## Contract

Every action proposal that reaches AgentPlane must bind to a Legal Core decision before runtime admission.

The required reference is:

`legal_core_decision_ref -> legal-core-decision:*`

The runtime gate then emits either:

- a runtime receipt for admitted work, or
- a denial receipt for blocked work.

Both outcomes are evidence.

## Required gates

| Gate | Purpose |
| --- | --- |
| `RuntimeAuthorityGate` | Blocks `unknown` and `prohibited` authority before sandbox allocation or runtime action. |
| `PurposeGate` | Ensures action purpose is compatible with authority, rights, and sensitivity. |
| `SafeProcessingGate` | Blocks unsafe rendering, unapproved external lookup, mutation, unscoped network behavior, and credential access by default. |
| `SandboxAllocationGate` | Makes sandbox allocation receipt-backed without implying execution or production parity. |
| `RuntimeReceiptGate` | Emits machine-readable receipts for admitted and denied actions. |
| `EvidencePromotionGate` | Prevents runtime outputs from promoting into evidence, semantic memory, graph edges, or report claims without Legal Core and claim-boundary receipts. |

## Preview-surface seed case

The seed case is the Finder / QuickLook / WebKit preview-surface investigation:

`Finder -> QuickLookUIService -> ANE-assisted preview activity -> Web/Web2 qldisplay -> WebKitLegacy guard fault`

The correct claim state is `unresolved_suspicious`.

AgentPlane policy for that case:

- static document triage may be admitted when authority is `first_party_defensive`;
- unsafe rendering remains blocked;
- external lookup from suspect provenance metadata remains blocked unless separately authorized;
- sandbox allocation does not claim execution;
- execution does not claim production parity;
- evidence promotion remains blocked until Legal Core and claim-boundary receipts exist.

## Files

- `schemas/legal-core/runtime-action-admission-legal-gate.v0.1.schema.json`
- `tests/fixtures/legal-core/runtime-action-admission.static-doc-triage.allowed.json`
- `tests/fixtures/legal-core/runtime-action-admission.unknown-authority.denied.json`

## Non-goals

- AgentPlane does not provide jurisdiction-specific legal advice.
- AgentPlane does not certify production readiness by itself.
- AgentPlane does not turn sandbox allocation into a production parity claim.
- AgentPlane does not promote runtime output into SynapseIQ, Sherlock, Holmes, MeshRush, CairnPath, GAIA, Ontogenesis, or Sociosphere without explicit Legal Core and claim-boundary receipts.
