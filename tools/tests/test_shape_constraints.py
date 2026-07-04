#!/usr/bin/env python3
"""§7 shape-constraint enforcement tests.

Run: python3 -m pytest -q tools/tests/test_shape_constraints.py
"""

from __future__ import annotations

import importlib.util
import os
import random
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
spec = importlib.util.spec_from_file_location("shape_constraints", os.path.join(_TOOLS, "shape_constraints.py"))
sc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sc
spec.loader.exec_module(sc)


def _sampler(rng):
    return {"severity": rng.uniform(0, 1), "verified": rng.uniform(0, 1), "unverified": rng.uniform(0, 1), "ambiguity": rng.uniform(0, 1)}


def test_monotone_function_passes():
    fn = lambda x: 2 * x["severity"] + x["verified"]
    c = sc.ShapeConstraint("severity", "monotone", "property_tested")
    assert sc.check(fn, c, _sampler, random.Random(1)).finding == sc.FINDING_OK


def test_non_monotone_function_is_violation():
    fn = lambda x: -3 * x["severity"]          # risk DECREASES with severity => wrong
    c = sc.ShapeConstraint("severity", "monotone", "property_tested")
    f = sc.check(fn, c, _sampler, random.Random(1))
    assert f.finding == sc.FINDING_VIOLATION and "monotonicity" in f.detail


def test_dominance_verified_over_unverified():
    fn = lambda x: 5 * x["verified"] + 1 * x["unverified"]      # verified helps more
    ok = sc.ShapeConstraint("verified", "dominance", "property_tested", dominates_over="unverified")
    assert sc.check(fn, ok, _sampler, random.Random(2)).finding == sc.FINDING_OK
    bad = lambda x: 1 * x["verified"] + 5 * x["unverified"]     # unverified dominates => violation
    assert sc.check(bad, ok, _sampler, random.Random(2)).finding == sc.FINDING_VIOLATION


def test_abstention_rate_monotone_in_ambiguity_is_the_ac_shape_guarantee():
    # abstention probability must be non-decreasing in ambiguity (gives AC a shape guarantee)
    fn = lambda x: min(1.0, 0.2 + 0.8 * x["ambiguity"])
    c = sc.ShapeConstraint("ambiguity", "monotone", "property_tested")
    assert sc.check(fn, c, _sampler, random.Random(3)).finding == sc.FINDING_OK


def test_certified_requires_certificate_id():
    fn = lambda x: x["severity"]
    missing = sc.ShapeConstraint("severity", "monotone", "certified")
    assert sc.check(fn, missing, _sampler).finding == sc.FINDING_VIOLATION
    present = sc.ShapeConstraint("severity", "monotone", "certified", certificate_id="lipvor-abc123")
    assert sc.check(fn, present, _sampler).finding == sc.FINDING_OK


def test_architectural_is_trusted():
    fn = lambda x: -x["severity"]   # would fail property test, but architectural is trusted-by-construction
    c = sc.ShapeConstraint("severity", "monotone", "architectural")
    assert sc.check(fn, c, _sampler).finding == sc.FINDING_OK


def test_enforce_aggregates_and_flags_any_violation():
    fn = lambda x: 2 * x["severity"] - 4 * x["ambiguity"]   # ok in severity, wrong in ambiguity
    constraints = [
        sc.ShapeConstraint("severity", "monotone", "property_tested"),
        sc.ShapeConstraint("ambiguity", "monotone", "property_tested"),
    ]
    findings = sc.enforce(fn, constraints, _sampler, random.Random(4))
    assert sc.any_violation(findings)
    assert [f.finding for f in findings] == [sc.FINDING_OK, sc.FINDING_VIOLATION]
