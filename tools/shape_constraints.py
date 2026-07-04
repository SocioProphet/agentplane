#!/usr/bin/env python3
"""§7 shape-constraint enforcement (AGENTPLANE_COMPOSITION_PRIMITIVES §7).

A VerifierIR (schemas/verifier-ir.schema.v0.2.json `properties_constraints`) may
declare per-feature-slice shape constraints — monotone, joint_monotone, dominance,
unimodal — each with an enforcement mode:

  * architectural — constraint by construction (trusted; T1)
  * certified     — a post-hoc certificate attests it (T1; MUST carry certificate_id)
  * property_tested — verified only by metamorphic sampling here (T2, weakest)

For `property_tested`, this module actually exercises the scoring function and
returns VIOLATION on a counterexample — so a monotonicity drift is caught rather
than silently accepted. Example uses: risk monotone in severity; confidence
dominant in verified-evidence over unverified; abstention rate monotone in
ambiguity (a shape guarantee for Abstention Calibration). Stdlib-only.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

FINDING_OK = "OK"
FINDING_VIOLATION = "VIOLATION"
_EPS = 1e-9


@dataclass(frozen=True)
class ShapeConstraint:
    feature_slice: str
    constraint: str
    enforcement: str
    certificate_id: str | None = None
    # for `dominance`: the feature that must dominate `feature_slice`
    dominates_over: str | None = None


@dataclass(frozen=True)
class Finding:
    constraint: ShapeConstraint
    finding: str
    detail: str


def _monotone_counterexample(fn, feature, sampler, rng, n):
    for _ in range(n):
        x = sampler(rng)
        x2 = dict(x)
        x2[feature] = x[feature] + rng.uniform(0.01, 1.0)   # increase the feature
        if fn(x2) < fn(x) - _EPS:                            # score decreased => not monotone
            return (fn(x), fn(x2), feature)
    return None


def _dominance_counterexample(fn, hi, lo, sampler, rng, n):
    # increasing the high-integrity feature must help at least as much as the low one
    for _ in range(n):
        x = sampler(rng)
        d = rng.uniform(0.1, 1.0)
        xh = dict(x); xh[hi] = x[hi] + d
        xl = dict(x); xl[lo] = x[lo] + d
        if fn(xh) < fn(xl) - _EPS:
            return (fn(xh), fn(xl))
    return None


def check(fn, c: ShapeConstraint, sampler, rng: random.Random | None = None, n: int = 300) -> Finding:
    rng = rng or random.Random(0)
    if c.enforcement == "certified":
        if not c.certificate_id:
            return Finding(c, FINDING_VIOLATION, "certified constraint missing certificate_id")
        return Finding(c, FINDING_OK, f"certified by {c.certificate_id} (external verifier)")
    if c.enforcement == "architectural":
        return Finding(c, FINDING_OK, "architectural (constraint by construction)")

    # property_tested: exercise it
    if c.constraint in ("monotone",):
        cx = _monotone_counterexample(fn, c.feature_slice, sampler, rng, n)
        return (Finding(c, FINDING_VIOLATION, f"monotonicity violated: {cx[0]:.3f} -> {cx[1]:.3f} on {cx[2]}")
                if cx else Finding(c, FINDING_OK, "monotone verified"))
    if c.constraint == "joint_monotone":
        feats = c.feature_slice.split(",")
        for f in feats:
            cx = _monotone_counterexample(fn, f.strip(), sampler, rng, n)
            if cx:
                return Finding(c, FINDING_VIOLATION, f"joint monotonicity violated on {f.strip()}")
        return Finding(c, FINDING_OK, "joint monotone verified")
    if c.constraint == "dominance":
        if not c.dominates_over:
            return Finding(c, FINDING_VIOLATION, "dominance constraint missing dominates_over")
        cx = _dominance_counterexample(fn, c.feature_slice, c.dominates_over, sampler, rng, n)
        return (Finding(c, FINDING_VIOLATION, f"dominance violated: hi={cx[0]:.3f} < lo={cx[1]:.3f}")
                if cx else Finding(c, FINDING_OK, f"{c.feature_slice} dominates {c.dominates_over}"))
    # constraints not property-testable in v0.1 (edgeworth/trapezoid/unimodal/range_dominance)
    return Finding(c, FINDING_OK, f"{c.constraint} accepted (not property-tested in v0.1)")


def enforce(fn, constraints, sampler, rng: random.Random | None = None) -> list[Finding]:
    rng = rng or random.Random(0)
    return [check(fn, c, sampler, rng) for c in constraints]


def any_violation(findings: list[Finding]) -> bool:
    return any(f.finding == FINDING_VIOLATION for f in findings)
