# Epistemic-hygiene runtime

The live, teeth-verified producer for the epistemic-governance Hygiene layer.
Turns the standard-rich / runtime-poor layer into a standing service:

- **CTEST runner** — `tools/hygiene_runtime.py:run_ctest()` produces a
  `CountertestRunArtifact` (schema `schemas/countertest-run-artifact.schema.json`).
- **Bias Passport producer** — `produce_bias_passport()` emits a
  `HygieneRunArtifact` (`hygiene_profile: bias-passport`).
- **Calibration Passport producer** — `produce_calibration_passport()` emits a
  `HygieneRunArtifact` (`hygiene_profile: calibration-passport`) carrying drift
  state.
- **Id-namespace enforcement** — every detector id is checked against the
  governed map vendored at `tools/epigov/detector-id-map.vendored.json`; an
  ungoverned id is REJECTED before emission.
- **Seal** — every artifact gets a proof-artifact-spine SHA-256 receipt
  (`seal()` / `verify_seal()`).

Run the teeth self-test (what CI runs, via `make validate-hygiene-runtime`):

```
python3 tools/hygiene_runtime.py --selftest
python3 tools/hygiene_runtime.py --emit-examples examples/receipts/epigov-hygiene-runtime
```

## Consume-not-fork

The governed detector-id map and set-1 bias catalog are authored in
`SocioProphet/sociosphere` (`standards/epistemic-governance/`). This runtime
vendors a byte-copy **projection** (with source SHA-256s in `_provenance`) and
enforces it. Teeth for the map itself live in sociosphere CI
(`validate_detector_id_map.py`). When the canonical map changes, regenerate the
vendored JSON.

## Seat under the Crown (bind-upward)

Seated under the Crown constitution — `hellgraph/docs/adr/0004-crown-telos-truth-constitution.md`
(**hellgraph#52**), whose follow-up item 1 names this exact gap ("Hygiene runtime
is standard-rich / runtime-poor … no CTEST runner, no bias-passport /
calibration-passport producer … id-namespace drift"). This is **hellgraph#53**.

| Upstream authority (ADR-0004) | Binding in this runtime |
| --- | --- |
| **Truth Engine — Test-Obligation**; invariant **T1**: "a TruthRecord with no TestObligation is unfalsifiable → void" | `run_ctest()`: a claim with no declared falsifier / no counter-test obligation → verdict `epistemically_void`. Mirrors the SILENT Phase-0 gate (evidence-intake-kernel#2). |
| Invariant **D1** — "Da'at cannot assert truth" = the SILENT firewall's affirming-the-consequent guard (evidence-intake-kernel#3) | `run_ctest()` rejects an affirming-the-consequent inference with `rejection_code: REJECTED_AFFIRMING_THE_CONSEQUENT` — the SAME rule, cross-referenced in `bias-catalog.yaml` as `LOGFALL.AFFIRMCONSEQ.V1`. |
| **Bias/Calibration Passport = per-participant reasoning credential** feeding Truth Records | `produce_bias_passport()` / `produce_calibration_passport()` emit sealed passports that a Truth Record can consume. |

Counter-test dispatch reuses, by reference, the Noetica `reasoner.ts`
`CTEST_ROUTING` (6 runnable CTESTs) and the counter-test gate (Noetica PR #570);
the Test-Obligation pattern reuses the SILENT firewall (evidence-intake-kernel
#2/#3). This runtime is the deterministic agentplane-side producer, not a fork of
those engines.
