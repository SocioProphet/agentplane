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


def test_certificate_id_alone_is_unverified_not_ok():
    """An id string is not evidence. Without a verifier the claim is UNVERIFIED."""
    fn = lambda x: x["severity"]
    present = sc.ShapeConstraint("severity", "monotone", "certified", certificate_id="lipvor-abc123")
    f = sc.check(fn, present, _sampler)
    assert f.finding == sc.FINDING_UNVERIFIED
    assert "not validated" in f.detail


def test_certificate_verifier_decides_when_supplied():
    fn = lambda x: x["severity"]
    c = sc.ShapeConstraint("severity", "monotone", "certified", certificate_id="lipvor-abc123")
    assert sc.check(fn, c, _sampler, certificate_verifier=lambda cid: True).finding == sc.FINDING_OK
    assert sc.check(fn, c, _sampler, certificate_verifier=lambda cid: False).finding == sc.FINDING_VIOLATION


def test_certificate_is_contradicted_by_a_failing_property_test():
    """A certificate cannot launder a function that demonstrably breaks the constraint."""
    fn = lambda x: -3 * x["severity"]
    c = sc.ShapeConstraint("severity", "monotone", "certified", certificate_id="lipvor-abc123")
    f = sc.check(fn, c, _sampler, random.Random(5))
    assert f.finding == sc.FINDING_VIOLATION and "contradicted" in f.detail


def test_architectural_claim_is_refuted_by_counterexample():
    """A "by construction" label is a claim about the function; a counterexample refutes it."""
    fn = lambda x: -x["severity"]   # non-monotone despite the architectural label
    c = sc.ShapeConstraint("severity", "monotone", "architectural")
    f = sc.check(fn, c, _sampler, random.Random(6))
    assert f.finding == sc.FINDING_VIOLATION and "refuted" in f.detail


def test_architectural_claim_that_holds_is_ok():
    fn = lambda x: 2 * x["severity"]
    c = sc.ShapeConstraint("severity", "monotone", "architectural")
    assert sc.check(fn, c, _sampler, random.Random(6)).finding == sc.FINDING_OK


def test_architectural_claim_for_untestable_kind_is_unverified():
    fn = lambda x: x["severity"]
    c = sc.ShapeConstraint("severity", "trapezoid", "architectural")
    f = sc.check(fn, c, _sampler)
    assert f.finding == sc.FINDING_UNVERIFIED


def test_untestable_constraint_kinds_are_unverified_not_ok():
    """The regression this module exists to prevent: silent OK for unchecked kinds."""
    fn = lambda x: x["severity"]
    for kind in ("edgeworth", "trapezoid", "range_dominance"):
        f = sc.check(fn, sc.ShapeConstraint("severity", kind, "property_tested"), _sampler)
        assert f.finding == sc.FINDING_UNVERIFIED, f"{kind} must not report OK unchecked"
        assert "not checked" in f.detail


def test_unimodal_is_now_property_tested():
    peak = lambda x: -((x["ambiguity"] - 0.5) ** 2)          # single peak at 0.5
    c = sc.ShapeConstraint("ambiguity", "unimodal", "property_tested")
    assert sc.check(peak, c, _sampler, random.Random(7)).finding == sc.FINDING_OK

    bimodal = lambda x: abs(x["ambiguity"] - 0.5)            # two modes at the ends
    f = sc.check(bimodal, c, _sampler, random.Random(7))
    assert f.finding == sc.FINDING_VIOLATION and "unimodality" in f.detail


def test_all_verified_requires_checked_and_held():
    """A gate must not treat never-checked as passing."""
    fn = lambda x: 2 * x["severity"]
    checked = [sc.ShapeConstraint("severity", "monotone", "property_tested")]
    unchecked = [sc.ShapeConstraint("severity", "trapezoid", "property_tested")]

    good = sc.enforce(fn, checked, _sampler, random.Random(8))
    assert sc.all_verified(good) and not sc.any_unverified(good)

    silent = sc.enforce(fn, unchecked, _sampler, random.Random(8))
    assert not sc.any_violation(silent), "unchecked is not a violation"
    assert sc.any_unverified(silent) and not sc.all_verified(silent), "but it is NOT passing"


def test_enforce_aggregates_and_flags_any_violation():
    fn = lambda x: 2 * x["severity"] - 4 * x["ambiguity"]   # ok in severity, wrong in ambiguity
    constraints = [
        sc.ShapeConstraint("severity", "monotone", "property_tested"),
        sc.ShapeConstraint("ambiguity", "monotone", "property_tested"),
    ]
    findings = sc.enforce(fn, constraints, _sampler, random.Random(4))
    assert sc.any_violation(findings)
    assert [f.finding for f in findings] == [sc.FINDING_OK, sc.FINDING_VIOLATION]


def test_accepted_certificate_cannot_launder_a_refuted_constraint():
    """Evidence of breakage outranks attestation that it holds."""
    fn = lambda x: -3 * x["severity"]          # demonstrably non-monotone
    c = sc.ShapeConstraint("severity", "monotone", "certified", certificate_id="lipvor-abc123")
    f = sc.check(fn, c, _sampler, random.Random(9), certificate_verifier=lambda _cid: True)
    assert f.finding == sc.FINDING_VIOLATION
    assert "contradicted" in f.detail


def test_certificate_still_ok_when_property_test_holds_and_verifier_accepts():
    fn = lambda x: 2 * x["severity"]
    c = sc.ShapeConstraint("severity", "monotone", "certified", certificate_id="lipvor-abc123")
    f = sc.check(fn, c, _sampler, random.Random(9), certificate_verifier=lambda _cid: True)
    assert f.finding == sc.FINDING_OK


def test_untestable_certified_kind_relies_on_the_verifier():
    """No property test exists for trapezoid, so the verifier is the only evidence."""
    fn = lambda x: x["severity"]
    c = sc.ShapeConstraint("severity", "trapezoid", "certified", certificate_id="cert-1")
    assert sc.check(fn, c, _sampler, certificate_verifier=lambda _cid: True).finding == sc.FINDING_OK
    assert sc.check(fn, c, _sampler, certificate_verifier=lambda _cid: False).finding == sc.FINDING_VIOLATION


def test_all_verified_is_false_on_an_empty_finding_set():
    """Deliberate fail-closed: "nothing evaluated" must not read as success."""
    assert sc.all_verified([]) is False
    assert sc.any_violation([]) is False
    assert sc.any_unverified([]) is False


def test_property_testable_constant_matches_dispatch():
    """The constant is authoritative: every listed kind must actually dispatch."""
    fn = lambda x: x["severity"]
    for kind in sc.PROPERTY_TESTABLE:
        c = sc.ShapeConstraint("severity", kind, "property_tested",
                               dominates_over="unverified" if kind == "dominance" else None)
        f = sc.check(fn, c, _sampler, random.Random(10))
        assert f.finding != sc.FINDING_UNVERIFIED, f"{kind} is listed testable but reported UNVERIFIED"


def test_unknown_enforcement_mode_is_a_violation_not_a_fallthrough():
    """A typo'd mode must not quietly land in the weakest branch and pass."""
    fn = lambda x: 2 * x["severity"]           # would PASS a property test
    c = sc.ShapeConstraint("severity", "monotone", "architecturaal")   # typo
    f = sc.check(fn, c, _sampler, random.Random(11))
    assert f.finding == sc.FINDING_VIOLATION
    assert "unknown enforcement mode" in f.detail


def test_every_declared_enforcement_mode_is_handled():
    fn = lambda x: 2 * x["severity"]
    for mode in sc.ENFORCEMENT_MODES:
        c = sc.ShapeConstraint("severity", "monotone", mode, certificate_id="cert-1")
        f = sc.check(fn, c, _sampler, random.Random(12))
        assert "unknown enforcement mode" not in f.detail, mode
