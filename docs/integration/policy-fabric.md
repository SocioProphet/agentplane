# Integration guide: policy-fabric → agentplane

This guide explains how `agentplane` should consume governed verdict artifacts and promotion eligibility outputs emitted by the Policy Fabric intell-agency slice.

For the runtime-governance seam, see [docs/runtime-governance/intell-agency-verdict-consumption-v0.md](../runtime-governance/intell-agency-verdict-consumption-v0.md).

---

## Purpose of the seam

`policy-fabric` is the canonical upstream home for the current intell-agency companion tranche.

That slice owns:
- typed policy and validation semantics
- rights-critical promotion rules
- verdict artifacts and fixture-controlled promotion behavior
- threshold rationale and review/evidence semantics

`agentplane` is the downstream execution-plane consumer.

`agentplane` should **consume** verdict outputs and release-eligibility semantics from Policy Fabric, not redefine them locally.

---

## What agentplane should consume

The minimum downstream consumption surface is:

1. verdict artifact (`verdicts.json` or equivalent envelope)
2. verdict explanation artifact (`verdict_explanations.json` or equivalent envelope)
3. policy bundle identity and version
4. rights-critical promotion status for the requested execution lane
5. release or fixture context when relevant

---

## Minimal execution rule

Before remote-eligible or governed execution proceeds, `agentplane` should be able to answer:

- which policy bundle governed this decision?
- is the requested domain rights-critical?
- did the governing verdict permit promotion?
- if blocked, which predicates failed?

If those questions cannot be answered, the execution path should be treated as incomplete for this slice.

---

## Recommended handoff shape

A narrow handoff envelope should include at least:

```json
{
  "policy_bundle_id": "...",
  "policy_bundle_version": "...",
  "verdict_artifact_ref": "...",
  "verdict_explanations_ref": "...",
  "domain": "protest",
  "rights_critical": true,
  "promote": false,
  "failed_predicates": [
    "rights_critical_requires_bijection",
    "stability_below_threshold"
  ]
}
```

`agentplane` does not need to own the full authored-policy model to consume this envelope.

---

## Execution behavior

### When promote = true

`agentplane` may continue into normal bundle validation, placement, and run flow.

### When promote = false

`agentplane` should fail closed for governed execution lanes and emit evidence that the run was blocked by upstream policy verdict semantics.

### When verdict material is missing

`agentplane` should not infer permissive behavior by default. Missing or incomplete verdict material should be treated as non-promotable until explicitly resolved.

---

## Evidence expectations

When `agentplane` consumes this seam, downstream artifacts should preserve:

- verdict artifact reference
- explanation artifact reference
- governing policy bundle id/version
- blocked/passed decision
- failed predicates when blocked

That allows replay and review artifacts to explain not just that a run was blocked, but **why** it was blocked.

---

## Non-goals

This guide does not require `agentplane` to:
- own Policy Fabric authored policy contracts
- own threshold calibration logic
- own fixture generation
- decide canonical policy meaning locally

Those remain upstream responsibilities.
