#!/usr/bin/env python3
"""Mellumwork tiering — grounds the T1/T2 falsification tiers in code.

The composition and trace-cfr specs cite a "Mellumwork falsification framework"
that was NOT locatable as an external artifact (audit 2026-07-03). It names a real
distinction we use throughout, so rather than leave the tiering asserted this module
makes it executable:

  * T1 — deterministic / formal / certified evidence: a PROOF. Permit-eligible.
  * T2 — empirical / sampled evidence: a TEST. Advisory / refreshed on drift.

Bindings we already produce map onto the tiers:
  CTRL243.evidence  exact -> T1,  verified -> T1 (with witness),  sampled -> T2
  §7 enforcement    architectural -> T1,  certified -> T1,  property_tested -> T2

Promotion rule: T2 -> T1 requires durable proof material (a certificate / verified
witness) — the same gate as CTRL243 `verified` promotion. Stdlib-only.
"""

from __future__ import annotations

T1 = "T1"   # deterministic / formal / certified — a proof
T2 = "T2"   # empirical / sampled — a test

_GRADE_TIER = {"exact": T1, "verified": T1, "sampled": T2}
_ENFORCEMENT_TIER = {"architectural": T1, "certified": T1, "property_tested": T2}


def tier_of_grade(evidence_grade: str) -> str | None:
    return _GRADE_TIER.get(evidence_grade)


def tier_of_enforcement(enforcement: str) -> str | None:
    return _ENFORCEMENT_TIER.get(enforcement)


def can_promote_to_T1(from_tier: str, has_proof: bool) -> bool:
    """T2 evidence may be promoted to T1 only with durable proof material."""
    if from_tier == T1:
        return True
    return from_tier == T2 and has_proof


def effective_tier(*, evidence_grade: str | None = None, enforcement: str | None = None, has_proof: bool = False) -> str:
    """The tier this evidence licenses. `verified` grade is a T2->T1 promotion and
    therefore requires a witness (has_proof); without it, it stays T2."""
    if evidence_grade == "verified" and not has_proof:
        return T2
    for tier in (tier_of_grade(evidence_grade or ""), tier_of_enforcement(enforcement or "")):
        if tier is not None:
            return tier
    return T2   # unknown provenance is empirical at best
