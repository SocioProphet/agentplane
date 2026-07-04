#!/usr/bin/env python3
"""Argument-level provenance taint on capability grants.

Implements AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC §11: the admission gate checks
*argument provenance*, not just tool identity. Capability grants (ObligationIR
`kind=resource`, §6/§13.1) carry a per-argument taint label in a Denning lattice
(lattice model of secure information flow). The gate closes the lethal-trifecta /
EchoLeak-class exfiltration path at the argument boundary (CaMeL, FIDES).

Model — INTEGRITY lattice.
    Order `a ⊑ b` reads "a is no more trusted than b"; ⊤ = most trusted, ⊥ = least.
    Taint propagation is the MEET (greatest lower bound) over a derived value's
    inputs: one untrusted input drags the whole value down to the least-trusted
    label. Admission of a sensitive argument requiring minimum integrity `req` is
    permitted iff the value's integrity `v` satisfies `req ⊑ v` (the value is at
    least as trusted as required). Untrusted-derived argument to a trusted sink =>
    VIOLATION.

This is a deterministic lattice check: T1, harness-owned (v = g_H(e)); the finding
maps to VerifierIR {OK, VIOLATION} -> StopGate. Stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass

FINDING_OK = "OK"
FINDING_VIOLATION = "VIOLATION"


class LatticeError(ValueError):
    """The supplied partial order is not a lattice (a pair lacks a unique lub/glb)."""


@dataclass(frozen=True)
class Violation:
    arg_name: str
    required: str
    actual: str
    origin: str


class Lattice:
    """A finite lattice from a covering (Hasse) relation.

    Args:
        elements: the label set.
        covers:   (lower, higher) pairs meaning `lower` is directly below `higher`.
                  The partial order is the reflexive-transitive closure.
    Raises:
        LatticeError if some pair has no unique least-upper-bound or greatest-lower-bound.
    """

    def __init__(self, elements: list[str], covers: list[tuple[str, str]]):
        self.elements = list(elements)
        eset = set(elements)
        for lo, hi in covers:
            if lo not in eset or hi not in eset:
                raise LatticeError(f"cover ({lo},{hi}) references unknown element")
        # reflexive-transitive closure of the covering relation -> leq
        self._leq: dict[tuple[str, str], bool] = {}
        reach = {e: {e} for e in elements}
        adj: dict[str, set[str]] = {e: set() for e in elements}
        for lo, hi in covers:
            adj[lo].add(hi)
        changed = True
        while changed:
            changed = False
            for e in elements:
                for m in list(reach[e]):
                    for nxt in adj[m]:
                        if nxt not in reach[e]:
                            reach[e].add(nxt)
                            changed = True
        for a in elements:
            for b in elements:
                self._leq[(a, b)] = b in reach[a]
        # validate: every pair has a unique lub and glb
        for a in elements:
            for b in elements:
                self._bound(a, b, upper=True)
                self._bound(a, b, upper=False)

    def leq(self, a: str, b: str) -> bool:
        """a ⊑ b : a is no more trusted than b."""
        try:
            return self._leq[(a, b)]
        except KeyError as e:
            raise LatticeError(f"unknown element in leq({a},{b})") from e

    def _bound(self, a: str, b: str, upper: bool) -> str:
        # upper: least upper bound (join); else greatest lower bound (meet)
        if upper:
            bounds = [x for x in self.elements if self.leq(a, x) and self.leq(b, x)]
            # the extremum is the one below all others in `bounds`
            extremum = [x for x in bounds if all(self.leq(x, y) for y in bounds)]
        else:
            bounds = [x for x in self.elements if self.leq(x, a) and self.leq(x, b)]
            extremum = [x for x in bounds if all(self.leq(y, x) for y in bounds)]
        if len(extremum) != 1:
            kind = "lub" if upper else "glb"
            raise LatticeError(f"({a},{b}) has no unique {kind}: candidates={extremum}")
        return extremum[0]

    def join(self, a: str, b: str) -> str:
        return self._bound(a, b, upper=True)

    def meet(self, a: str, b: str) -> str:
        return self._bound(a, b, upper=False)

    def propagate(self, labels: list[str]) -> str:
        """Integrity taint of a value derived from inputs = meet over input labels.

        One untrusted input drags the derived value to the least-trusted label.
        """
        if not labels:
            raise LatticeError("propagate requires >=1 input label")
        acc = labels[0]
        for lab in labels[1:]:
            acc = self.meet(acc, lab)
        return acc


def integrity_lattice() -> Lattice:
    """Canonical 3-level integrity chain: UNTRUSTED ⊏ SANDBOXED ⊏ TRUSTED."""
    return Lattice(
        elements=["UNTRUSTED", "SANDBOXED", "TRUSTED"],
        covers=[("UNTRUSTED", "SANDBOXED"), ("SANDBOXED", "TRUSTED")],
    )


def admit(
    arg_labels: dict[str, str],
    required: dict[str, str],
    lattice: Lattice,
    origins: dict[str, str] | None = None,
) -> tuple[str, list[Violation]]:
    """Admission gate over argument provenance.

    Args:
        arg_labels: arg_name -> the value's (already-propagated) integrity label.
        required:   arg_name -> minimum integrity the capability demands for that arg.
        lattice:    the integrity lattice.
        origins:    optional arg_name -> provenance descriptor, for the witness.
    Returns:
        (finding, violations). finding = VIOLATION iff any required arg's value is
        not at least as trusted as required (i.e. NOT required ⊑ value).
    """
    origins = origins or {}
    violations: list[Violation] = []
    for arg, req in required.items():
        actual = arg_labels.get(arg)
        if actual is None:
            # a required-labeled arg with no provenance is treated as the lattice
            # bottom (least trusted): the element below every other element.
            actual = next(e for e in lattice.elements if all(lattice.leq(e, x) for x in lattice.elements))
        if not lattice.leq(req, actual):
            violations.append(Violation(arg_name=arg, required=req, actual=actual, origin=origins.get(arg, "unknown")))
    return (FINDING_VIOLATION if violations else FINDING_OK), violations
