# Banking Twin Execution Bundles (Staging Tranche)

This tranche stages first banking-oriented Agentplane bundles for the banking-twin initiative.

Bundles added here:
- `stress-runner`
- `capital-rollforward`
- `filing-assembler`
- `policy-audit`

These are **staging bundles**, not final production bundles. Their purpose is to:
1. establish stable bundle names and artifact directories,
2. bind banking execution lanes to policy-pack references,
3. ensure replay/evidence expectations are visible before runtime services are implemented.

Expected upstream semantic and contract refs:
- GAIA banking-firm profile + banking domains
- Ontogenesis banking ontology tranche
- standards-storage banking contracts and benchmark pack
- TriTRPC banking service catalog and transport binding

Expected evidence outputs per run:
- ValidationArtifact
- PlacementDecision
- RunArtifact
- ReplayArtifact

Expected next step after this tranche:
- wire these bundles into policy imports and runtime-governance notes
- add banking example receipts once the first vertical slice exists
- add real smoke scripts that validate input refs and emit run outputs
