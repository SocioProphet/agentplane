#!/usr/bin/env python3
"""Monoid-constrained sidechain receipt fold.

Implements AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC §4: a parent verdict over child
agents is
    R_parent = phi( fold_{i in children} psi(R_i) )
where the fold operator MUST be a commutative monoid (associative, commutative,
identity). Commutativity is exactly what makes ReceiptIR replay deterministic
regardless of child completion order (§14.1). For *blame* (not success) the
operator SHOULD be an abelian group (monoid + inverses) for signed, credit-
conserving flow (§10 AttributionIR).

Two canonical algebras:
  * verdict_monoid  — success aggregation: most-cautious-wins over StopGate verdicts
    (FAIL > REVIEW > INDETERMINATE > PASS), identity PASS. Commutative, associative,
    idempotent => a commutative monoid. This is the StopGate partial-verdict
    aggregation (WO-0.C / §13.4).
  * blame_group     — signed integer credit, op +, identity 0, inverse negate.

Binds schemas/receipt-fold.schema.v0.1.json. Stdlib-only.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Algebra:
    name: str
    op: Callable[[Any, Any], Any]
    identity: Any
    is_group: bool = False
    inverse: Callable[[Any], Any] | None = None


# --------------------------------------------------------------------------- #
# Canonical algebras
# --------------------------------------------------------------------------- #
# Caution ranking for success aggregation (matches STATUS §2 / WO-0.C).
_CAUTION = {"PASS": 0, "INDETERMINATE": 1, "REVIEW": 2, "FAIL": 3}


def _most_cautious(a: str, b: str) -> str:
    return a if _CAUTION[a] >= _CAUTION[b] else b


verdict_monoid = Algebra(name="verdict_monoid", op=_most_cautious, identity="PASS")

blame_group = Algebra(
    name="blame_group",
    op=lambda a, b: a + b,
    identity=0,
    is_group=True,
    inverse=lambda a: -a,
)


# --------------------------------------------------------------------------- #
# Fold + determinism
# --------------------------------------------------------------------------- #
def fold(values: list[Any], algebra: Algebra) -> Any:
    """Left-fold with the algebra's identity as the seed."""
    acc = algebra.identity
    for v in values:
        acc = algebra.op(acc, v)
    return acc


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def permutation_invariant(values: list[Any], algebra: Algebra, seed: int = 0) -> bool:
    """§14.1 conformance: the parent receipt hash is identical under child reorder.

    n <= 6: check every permutation. n > 6: identity + 120 random permutations + reverse.
    """
    base = _canonical_hash(fold(values, algebra))
    n = len(values)
    if n <= 6:
        perms = itertools.permutations(values)
    else:
        rng = random.Random(seed)
        perms_list = [list(values), list(reversed(values))]
        for _ in range(120):
            p = list(values)
            rng.shuffle(p)
            perms_list.append(p)
        perms = iter(perms_list)
    return all(_canonical_hash(fold(list(p), algebra)) == base for p in perms)


# --------------------------------------------------------------------------- #
# Axiom checks (§14.2)
# --------------------------------------------------------------------------- #
def check_axioms(algebra: Algebra, sample: list[Any]) -> dict[str, bool]:
    """Verify monoid (assoc/comm/identity) and, for a group, inverse, over `sample`."""
    op, e = algebra.op, algebra.identity
    assoc = all(op(op(a, b), c) == op(a, op(b, c)) for a in sample for b in sample for c in sample)
    comm = all(op(a, b) == op(b, a) for a in sample for b in sample)
    ident = all(op(a, e) == a and op(e, a) == a for a in sample)
    result = {"associative": assoc, "commutative": comm, "identity": ident}
    if algebra.is_group:
        assert algebra.inverse is not None
        result["inverse"] = all(op(a, algebra.inverse(a)) == e for a in sample)
    return result
