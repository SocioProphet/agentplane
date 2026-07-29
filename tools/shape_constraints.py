#!/usr/bin/env python3
"""§7 shape-constraint enforcement (AGENTPLANE_COMPOSITION_PRIMITIVES §7).

A VerifierIR (schemas/verifier-ir.schema.v0.2.json `properties_constraints`) may
declare per-feature-slice shape constraints — monotone, joint_monotone, dominance,
edgeworth, trapezoid, unimodal, range_dominance — each with an enforcement mode:

  * architectural   — claimed true by construction (T1)
  * certified       — a post-hoc certificate attests it (T1; MUST carry certificate_id)
  * property_tested — verified by metamorphic sampling here (T2, weakest but real)

THREE VERDICTS, NOT TWO. `UNVERIFIED` exists because the previous revision
returned OK for everything it could not actually check: constraint kinds with no
property test ("accepted (not property-tested in v0.1)"), every `architectural`
claim, and every `certified` claim whose certificate_id was merely a non-empty
string. Four of the schema's seven constraint kinds and two of its three
enforcement modes therefore reported OK without a single check running. A caller
gating on "no violations" could not distinguish a constraint that had been
verified from one that had never been examined.

OK means checked and held. VIOLATION means checked and broken. UNVERIFIED means
not checked — and a gate must treat it as not-passing (see `all_verified`).

Opportunistic testing: an `architectural` or `certified` claim is still property-
tested when the constraint kind supports it. "True by construction" is a claim
about the function, and a counterexample refutes it regardless of how it was
labelled — so a testable architectural claim that fails yields VIOLATION, not
trust. Only genuinely untestable combinations fall through to UNVERIFIED.

Stdlib-only.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

FINDING_OK = "OK"
FINDING_VIOLATION = "VIOLATION"
FINDING_UNVERIFIED = "UNVERIFIED"
_EPS = 1e-9

#: Constraint kinds this module can actually exercise. Anything outside this set
#: cannot be certified by property testing and must report UNVERIFIED.
PROPERTY_TESTABLE = frozenset({"monotone", "joint_monotone", "dominance", "unimodal"})


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


def _feature_range(feature, sampler, rng, probes=64):
    """Empirical range of `feature` under the sampler, so the sweep matches the domain."""
    values = [sampler(rng)[feature] for _ in range(probes)]
    lo, hi = min(values), max(values)
    if hi - lo < _EPS:
        hi = lo + 1.0
    return lo, hi


def _unimodal_counterexample(fn, feature, sampler, rng, n, steps=25):
    """Sweep `feature` across its range from several random base points.

    Unimodal = non-decreasing up to a single peak, then non-increasing. A dip
    before the peak or a rise after it means there is more than one mode.
    """
    lo, hi = _feature_range(feature, sampler, rng)
    span = hi - lo
    sweeps = max(1, n // steps)
    for _ in range(sweeps):
        base = sampler(rng)
        xs = [lo + span * (i / (steps - 1)) for i in range(steps)]
        ys = []
        for t in xs:
            point = dict(base)
            point[feature] = t
            ys.append(fn(point))
        peak = max(range(steps), key=lambda i: ys[i])
        for i in range(peak):                       # must be rising up to the peak
            if ys[i + 1] < ys[i] - _EPS:
                return (feature, xs[i], ys[i], xs[i + 1], ys[i + 1], "dip before peak")
        for i in range(peak, steps - 1):            # must be falling after it
            if ys[i + 1] > ys[i] + _EPS:
                return (feature, xs[i], ys[i], xs[i + 1], ys[i + 1], "rise after peak")
    return None


def _property_test(fn, c: ShapeConstraint, sampler, rng, n) -> Finding | None:
    """Run the property test for `c` if its kind supports one; else None.

    PROPERTY_TESTABLE gates dispatch so the constant cannot drift away from the
    implementation: a kind listed there but unhandled below raises rather than
    silently returning None (which would read as "untestable" and produce a
    false UNVERIFIED).
    """
    if c.constraint not in PROPERTY_TESTABLE:
        return None
    if c.constraint == "monotone":
        cx = _monotone_counterexample(fn, c.feature_slice, sampler, rng, n)
        return (Finding(c, FINDING_VIOLATION, f"monotonicity violated: {cx[0]:.3f} -> {cx[1]:.3f} on {cx[2]}")
                if cx else Finding(c, FINDING_OK, "monotone verified"))
    if c.constraint == "joint_monotone":
        for f in c.feature_slice.split(","):
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
    if c.constraint == "unimodal":
        cx = _unimodal_counterexample(fn, c.feature_slice, sampler, rng, n)
        return (Finding(c, FINDING_VIOLATION,
                        f"unimodality violated on {cx[0]}: {cx[5]} "
                        f"({cx[1]:.3f}->{cx[3]:.3f} gave {cx[2]:.3f}->{cx[4]:.3f})")
                if cx else Finding(c, FINDING_OK, "unimodal verified"))
    raise AssertionError(
        f"{c.constraint!r} is listed in PROPERTY_TESTABLE but has no dispatch branch"
    )


def check(
    fn,
    c: ShapeConstraint,
    sampler,
    rng: random.Random | None = None,
    n: int = 300,
    certificate_verifier: Callable[[str], bool] | None = None,
) -> Finding:
    """Evaluate one shape constraint.

    `certificate_verifier` is an optional callable taking the certificate id and
    returning True/False. Without it, a `certified` constraint is UNVERIFIED: the
    presence of an id string is not evidence that anything was certified.
    """
    rng = rng or random.Random(0)

    if c.enforcement == "certified":
        if not c.certificate_id:
            return Finding(c, FINDING_VIOLATION, "certified constraint missing certificate_id")

        # Refutation runs FIRST and unconditionally. Evidence that the constraint
        # is broken outranks any attestation that it holds — otherwise an accepted
        # certificate would launder a function this module can demonstrably refute,
        # which is the exact "asserted but never checked" failure this file exists
        # to remove.
        probe = _property_test(fn, c, sampler, rng, n)
        if probe is not None and probe.finding == FINDING_VIOLATION:
            return Finding(c, FINDING_VIOLATION,
                           f"certificate {c.certificate_id} contradicted by property test: {probe.detail}")

        if certificate_verifier is None:
            return Finding(c, FINDING_UNVERIFIED,
                           f"certificate {c.certificate_id} not validated (no certificate_verifier supplied)")
        if not certificate_verifier(c.certificate_id):
            return Finding(c, FINDING_VIOLATION, f"certificate {c.certificate_id} rejected by verifier")
        return Finding(c, FINDING_OK, f"certified by {c.certificate_id} (verifier accepted)")

    if c.enforcement == "architectural":
        # "By construction" is a claim about the function; a counterexample refutes it.
        probe = _property_test(fn, c, sampler, rng, n)
        if probe is None:
            return Finding(c, FINDING_UNVERIFIED,
                           f"architectural claim for {c.constraint} is not property-testable — not checked")
        if probe.finding == FINDING_VIOLATION:
            return Finding(c, FINDING_VIOLATION, f"architectural claim refuted: {probe.detail}")
        return Finding(c, FINDING_OK, f"architectural claim held under property test ({c.constraint})")

    # property_tested
    result = _property_test(fn, c, sampler, rng, n)
    if result is None:
        return Finding(c, FINDING_UNVERIFIED,
                       f"{c.constraint} has no property test in this module — not checked")
    return result


def enforce(
    fn,
    constraints,
    sampler,
    rng: random.Random | None = None,
    certificate_verifier: Callable[[str], bool] | None = None,
) -> list[Finding]:
    rng = rng or random.Random(0)
    return [check(fn, c, sampler, rng, certificate_verifier=certificate_verifier) for c in constraints]


def any_violation(findings: list[Finding]) -> bool:
    """A constraint was checked and found broken."""
    return any(f.finding == FINDING_VIOLATION for f in findings)


def any_unverified(findings: list[Finding]) -> bool:
    """A constraint was never checked. Not the same as passing."""
    return any(f.finding == FINDING_UNVERIFIED for f in findings)


def all_verified(findings: list[Finding]) -> bool:
    """Non-empty AND every constraint checked and held — what a gate should require.

    Prefer this over `not any_violation(...)`, which treats never-checked as fine.

    An EMPTY findings list returns False, deliberately, and not by the usual
    vacuous-truth convention: "nothing was evaluated" is the state this module
    exists to stop reporting as success. A caller that legitimately has no
    constraints should branch on that explicitly rather than read it as verified.
    """
    return bool(findings) and all(f.finding == FINDING_OK for f in findings)
