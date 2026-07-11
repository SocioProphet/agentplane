#!/usr/bin/env python3
"""CO-7 promotion gating validator (AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC §14.7).

Promotion of an item from trace -> candidate, or candidate -> durable, is a
governed ACTION and MUST NOT occur except under a POS verdict. Negative
fixtures MUST fail this check and pass the correctly-rejected assertion,
including rejection for the declared exception class (§13.9 closed enum).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "composition-primitives"

TIERS = ("trace", "candidate", "durable")
PROMOTION_STEPS = {("trace", "candidate"), ("candidate", "durable")}
RECEIPT_REQUIRED = ("verdict", "policy_id", "evidence_digest",
                    "actor_id", "prior_state", "post_state")
VERDICTS = ("POS", "ZERO", "NEG")

# §13.9 — closed enum; no catch-all member. Any unmatched condition is a spec bug.
EXCEPTION_CLASSES = (
    "EXC_OUT_OF_GRANT",
    "EXC_RECEIPT_DIVERGENCE",
    "EXC_UNGATED_PROMOTION",
    "EXC_STALE_EVIDENCE",
    "EXC_REVOKED_GRANT",
    "EXC_QUARANTINE_TAINT",
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def check_promotion(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (exception_class, message) problems; empty list == promotion admitted."""
    problems: list[tuple[str, str]] = []

    from_tier = data.get("from_tier")
    to_tier = data.get("to_tier")
    if (from_tier, to_tier) not in PROMOTION_STEPS:
        problems.append(("EXC_UNGATED_PROMOTION",
                         f"not an allowed promotion step: {from_tier} -> {to_tier}"))
        return problems

    receipt = data.get("promotion_receipt")
    if not isinstance(receipt, dict):
        problems.append(("EXC_UNGATED_PROMOTION",
                         "tier change with no promotion receipt (CO-7.1)"))
        return problems

    missing = [f for f in RECEIPT_REQUIRED if not receipt.get(f)]
    if missing:
        problems.append(("EXC_UNGATED_PROMOTION",
                         f"receipt missing required fields {missing} (CO-7.1 / §13.8)"))
        return problems

    verdict = receipt["verdict"]
    if verdict not in VERDICTS:
        problems.append(("EXC_UNGATED_PROMOTION",
                         f"unknown verdict {verdict!r}; not resolvable to POS (CO-7.4)"))
        return problems

    if verdict != "POS":
        # CO-7.2: ZERO holds at current tier, no soft-allow / timeout-to-promote.
        # CO-7.3: NEG tombstones; item retained in trace. Either way no tier change.
        problems.append(("EXC_UNGATED_PROMOTION",
                         f"tier change under {verdict} verdict; only POS promotes "
                         "(CO-7.2/CO-7.3)"))

    if (receipt["prior_state"], receipt["post_state"]) != (from_tier, to_tier):
        problems.append(("EXC_RECEIPT_DIVERGENCE",
                         "attested prior/post state != observed from/to tier"))

    registry = data.get("policy_registry") or []
    if receipt["policy_id"] not in registry:
        problems.append(("EXC_UNGATED_PROMOTION",
                         f"policy_id {receipt['policy_id']!r} does not resolve; "
                         "receipt cannot be resolved to a POS verdict -> quarantine (CO-7.4)"))

    if to_tier == "durable":
        for item in data.get("evidence_closure") or []:
            if item.get("status") in ("quarantined", "retracted"):
                problems.append(("EXC_QUARANTINE_TAINT",
                                 f"evidence closure item {item.get('item_id')!r} is "
                                 f"{item['status']}; provenance is transitive (CO-7.5)"))

    return problems


def main() -> int:
    failed = False

    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid composition-primitives promotion fixtures")

    for path in valids:
        problems = check_promotion(load_json(path))
        if problems:
            print(f"FAIL (valid): {path.name}")
            for exc, msg in problems:
                print(f"  - [{exc}] {msg}")
            failed = True
        else:
            print(f"ok: {path.name}")

    rejects = sorted(FIXTURES.glob("neg-*.json"))
    if not rejects:
        raise SystemExit("missing neg-* composition-primitives promotion fixtures")

    for path in rejects:
        data = load_json(path)
        expected = data.get("expected_exception")
        if expected not in EXCEPTION_CLASSES:
            print(f"FAIL (fixture bug): {path.name} expected_exception {expected!r} "
                  "not in closed enum (§13.9)")
            failed = True
            continue
        problems = check_promotion(data)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        elif expected not in {exc for exc, _ in problems}:
            print(f"FAIL (rejected for wrong class): {path.name} "
                  f"expected {expected}, got {[exc for exc, _ in problems]}")
            failed = True
        else:
            print(f"ok (correctly rejected, {expected}): {path.name}")

    print(("PASS" if not failed else "FAIL")
          + f": CO-7 promotion gate — {len(valids)} valid, {len(rejects)} reject")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
