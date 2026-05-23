# Integrity Evidence Contract v0.1

## Purpose

`IntegrityEvidenceRequest v0.1` and `IntegrityEvidenceResult v0.1` define the evidence boundary for future recovery-style validation without adding any runtime path.

The contract records safe-root scope, governed admission reference, authority posture, candidate paths, and digest evidence. It is evidence-only.

## Artifacts

Schemas:

```text
schemas/receipts/integrity-evidence-request.v0.1.schema.json
schemas/receipts/integrity-evidence-result.v0.1.schema.json
```

Validator:

```text
tools/check_integrity_evidence.py
```

Tests:

```text
tools/tests/test_integrity_evidence.py
```

Fixtures:

```text
tests/fixtures/receipts/integrity-evidence-request.valid.json
tests/fixtures/receipts/integrity-evidence-result.valid.json
tests/fixtures/receipts/integrity-evidence-request.missing-boundary.invalid.json
tests/fixtures/receipts/integrity-evidence-request.path-outside-root.invalid.json
tests/fixtures/receipts/integrity-evidence-request.suspended-authority.invalid.json
```

## Request invariants

A valid request requires:

- non-empty boundary evidence reference;
- `admission_ref` beginning with `attempt-admission-receipt:`;
- authority status not suspended or revoked;
- a declared safe root;
- at least one path inside the declared root;
- before and expected digests bound with `sha256:`.

## Result invariants

A valid result requires:

- request reference;
- boundary evidence reference;
- admission reference;
- authority-state reference;
- declared safe root;
- path result set;
- observed and expected digests;
- `matches_expected` equal to the digest comparison;
- `recorded` status only when observed digest matches expected digest.

## Validation

```bash
python3 tools/check_integrity_evidence.py tests/fixtures/receipts/integrity-evidence-request.valid.json
python3 tools/check_integrity_evidence.py tests/fixtures/receipts/integrity-evidence-result.valid.json
python3 -m pytest -q tools/tests/test_integrity_evidence.py
```

## Non-goals

This contract does not add:

- filesystem mutation;
- recovery action implementation;
- verifier execution;
- provider calls;
- network access;
- authority update;
- budget settlement integration.

A future implementation must be a separate policy-gated tranche.
