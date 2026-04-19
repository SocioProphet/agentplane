# Integration guide: sourceos-spec local-first release contracts → agentplane

This guide explains how `agentplane` should consume the local-first release-control contract family published from `SourceOS-Linux/sourceos-spec`.

The canonical upstream object family is introduced in:

- `ReleaseSet`
- `BootReleaseSet`
- `EnrollmentToken`
- `Fingerprint`
- `ExperienceProfile`
- `IsolationProfile`

`agentplane` is the downstream execution-plane consumer of those objects. It should not redefine them locally.

---

## Purpose of the seam

`sourceos-spec` owns the machine-readable typed contracts for local-first release assignment and post-apply attestation.

`agentplane` owns:

- bundle validation and execution eligibility
- placement and replay/evidence behavior
- downstream apply/rollback execution semantics
- runtime-side consumption of release assignment and fingerprint evidence

---

## What agentplane should consume

The minimum downstream consumption surface is:

1. `ReleaseSet`
2. optional `BootReleaseSet`
3. optional `EnrollmentToken` when boot/recovery or first-join flow is required
4. `ExperienceProfile` reference
5. `IsolationProfile` reference
6. `Fingerprint` after apply

---

## Minimal execution rule

Before a local-first apply or rollback path proceeds, `agentplane` should be able to answer:

- which `ReleaseSet` governs this target?
- which experience and isolation profiles are attached?
- is there a required boot/recovery companion set?
- is there a valid enrollment token when the requested path requires one?
- after apply, did the emitted fingerprint remain compliant with the assigned release?

If those questions cannot be answered, the path should be treated as incomplete for this slice.

---

## Recommended handoff shape

A narrow downstream handoff envelope should include at least:

```json
{
  "release_set_ref": "rs_local_0001",
  "boot_release_set_ref": "brs_local_0001",
  "experience_profile_ref": "xp_local_0001",
  "isolation_profile_ref": "iso_local_0001",
  "enrollment_token_ref": "tok_local_0001",
  "target_id": "m2-control-node-01"
}
```

After apply, downstream artifacts should preserve:

```json
{
  "release_set_ref": "rs_local_0001",
  "fingerprint_ref": "fp_local_0001",
  "compliance_status": "compliant"
}
```

---

## Execution behavior

### When the assignment is complete

`agentplane` may continue into normal validation, placement, apply, and evidence flow.

### When boot/recovery authorization is required

`agentplane` should require the `BootReleaseSet` and any valid `EnrollmentToken` expected by that path.

### When fingerprint evidence is missing or non-compliant

`agentplane` should not silently mark the assignment successful. Missing or drifted fingerprint evidence should remain visible in downstream artifacts and replay surfaces.

---

## Evidence expectations

Downstream artifacts should preserve:

- `ReleaseSet` reference
- `BootReleaseSet` reference when used
- `ExperienceProfile` reference
- `IsolationProfile` reference
- `EnrollmentToken` reference when used
- `Fingerprint` reference
- compliance outcome (`compliant`, `drifted`, `unknown`, `failed`)

That lets replay and review explain not just that a local-first apply occurred, but whether the resulting host actually matched the assigned release contract.

---

## Non-goals

This guide does not require `agentplane` to:

- become the canonical schema source
- own higher-level workstation/bootstrap semantics
- define transport bindings for these objects

Those remain upstream responsibilities in `sourceos-spec` and adjacent repos.
