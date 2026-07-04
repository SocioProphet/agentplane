#!/usr/bin/env python3
"""§14.1 permutation-invariance + §14.2 axiom conformance for receipt_fold.

Run: python3 -m pytest -q tools/tests/test_receipt_fold.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_MOD = os.path.join(_HERE, os.pardir, "receipt_fold.py")
_spec = importlib.util.spec_from_file_location("receipt_fold", _MOD)
rf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = rf
_spec.loader.exec_module(rf)


def test_verdict_monoid_axioms():
    sample = ["PASS", "REVIEW", "VIOLATION" if False else "FAIL", "INDETERMINATE"]
    ax = rf.check_axioms(rf.verdict_monoid, sample)
    assert ax == {"associative": True, "commutative": True, "identity": True}


def test_verdict_most_cautious_wins():
    assert rf.fold(["PASS", "REVIEW", "PASS"], rf.verdict_monoid) == "REVIEW"
    assert rf.fold(["REVIEW", "FAIL", "INDETERMINATE"], rf.verdict_monoid) == "FAIL"
    assert rf.fold([], rf.verdict_monoid) == "PASS"          # identity
    assert rf.fold(["PASS", "PASS"], rf.verdict_monoid) == "PASS"


def test_blame_group_axioms_including_inverse():
    sample = [-3, -1, 0, 2, 5]
    ax = rf.check_axioms(rf.blame_group, sample)
    assert ax == {"associative": True, "commutative": True, "identity": True, "inverse": True}


def test_permutation_invariance_small_and_large():
    # n <= 6: exhaustive
    assert rf.permutation_invariant(["PASS", "REVIEW", "FAIL", "INDETERMINATE"], rf.verdict_monoid)
    # n > 6: sampled
    big = ["PASS", "REVIEW", "FAIL", "INDETERMINATE", "PASS", "REVIEW", "FAIL", "PASS"]
    assert rf.permutation_invariant(big, rf.verdict_monoid, seed=7)
    # blame group is also order-independent
    assert rf.permutation_invariant([-3, -1, 0, 2, 5, 8, 13], rf.blame_group, seed=1)


def test_non_commutative_op_is_caught():
    # string concat: associative + has identity "" but NOT commutative -> replay-unsafe
    concat = rf.Algebra(name="concat", op=lambda a, b: a + b, identity="")
    ax = rf.check_axioms(concat, ["a", "b", "c"])
    assert ax["associative"] and ax["identity"]
    assert ax["commutative"] is False
    # and the §14.1 permutation test must FAIL for it
    assert rf.permutation_invariant(["a", "b", "c"], concat) is False
