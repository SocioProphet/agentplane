#!/usr/bin/env python3
"""Mellumwork T1/T2 tiering tests.

Run: python3 -m pytest -q tools/tests/test_mellumwork.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
spec = importlib.util.spec_from_file_location("mellumwork", os.path.join(_TOOLS, "mellumwork.py"))
mw = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mw
spec.loader.exec_module(mw)


def test_grade_tiers():
    assert mw.tier_of_grade("exact") == mw.T1
    assert mw.tier_of_grade("sampled") == mw.T2
    assert mw.tier_of_grade("verified") == mw.T1


def test_enforcement_tiers():
    assert mw.tier_of_enforcement("architectural") == mw.T1
    assert mw.tier_of_enforcement("certified") == mw.T1
    assert mw.tier_of_enforcement("property_tested") == mw.T2


def test_promotion_requires_proof():
    assert mw.can_promote_to_T1(mw.T2, has_proof=True)
    assert not mw.can_promote_to_T1(mw.T2, has_proof=False)
    assert mw.can_promote_to_T1(mw.T1, has_proof=False)


def test_verified_without_witness_stays_t2():
    # 'verified' is a T2->T1 promotion; no witness => stays empirical
    assert mw.effective_tier(evidence_grade="verified", has_proof=False) == mw.T2
    assert mw.effective_tier(evidence_grade="verified", has_proof=True) == mw.T1


def test_hammock_exact_is_t1_interval_sampled_is_t2():
    # R_H exact -> T1; R_I under irreducibility (sampled) -> T2
    assert mw.effective_tier(evidence_grade="exact") == mw.T1
    assert mw.effective_tier(evidence_grade="sampled") == mw.T2


def test_unknown_provenance_is_empirical():
    assert mw.effective_tier() == mw.T2
