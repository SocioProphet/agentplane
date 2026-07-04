#!/usr/bin/env python3
"""Conformal Risk Control for the INDETERMINATE abstention gate.

Implements AGENTPLANE_COMPOSITION_PRIMITIVES_SPEC §8: replace the heuristic
INDETERMINATE threshold with a distribution-free abstention rule carrying a
declared risk budget `alpha`. This is the change that upgrades the Abstention
Calibration moat metric from heuristic to defensible.

Method: split Conformal Risk Control (Angelopoulos et al. 2024). Given a
harness-held, labeled calibration set of (nonconformity score s, was-correct)
pairs and a risk budget `alpha`, we accept a test point (emit the engine's real
verdict) iff its score `s <= lambda_hat`, else we abstain (INDETERMINATE).

Nonconformity score convention: HIGH s = closer to the decision boundary / less
recoverable => more likely wrong => should abstain. For SP-TRACE-CFR the score is
an engine-agreement-and-coverage margin (1 - fraction of the claimed span both
engines recovered in agreement); any monotone uncertainty score works.

GUARANTEE (stated precisely, not overclaimed). With loss
    L_i(lambda) = 1[ s_i <= lambda  AND  not correct_i ]   (accepted & wrong)
which is monotone non-decreasing in lambda, CRC picks
    lambda_hat = sup{ lambda : ( n * Rhat_n(lambda) + B ) / (n + 1) <= alpha }
and yields the MARGINAL bound
    E[ L_test(lambda_hat) ] = P( accept AND wrong ) <= alpha .
This bounds the accepted-and-wrong *rate*. It is NOT a conditional
P(wrong | accepted) guarantee — that is not distribution-free without stronger
assumptions. Consumers MUST read the guarantee as the marginal accepted-error rate.

Streaming (§8 anytime-valid) and chained-gate composition (§8 PASC joint coverage)
are declared extension points below; v0.1 implements the fixed-split guarantee.

Stdlib-only (repo zero-dependency posture). See schemas/verifier-ir.schema.v0.2.json
`conformal` block, which parameterizes this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

LOSS_BOUND = 1.0  # B: 0-1 loss

ACCEPT = "ACCEPT"          # emit the engine's real verdict
ABSTAIN = "INDETERMINATE"  # override to INDETERMINATE


@dataclass(frozen=True)
class CalibratedGate:
    """Result of calibration: the accept threshold plus provenance for the receipt."""
    lambda_hat: float
    alpha: float
    n_calibration: int
    alpha_feasible: bool          # False => alpha below the finite-sample floor 1/(n+1); abstain-all
    finite_sample_floor: float    # 1/(n+1)

    def classify(self, score: float) -> str:
        """ACCEPT (emit real verdict) iff score <= lambda_hat, else INDETERMINATE."""
        return ACCEPT if score <= self.lambda_hat else ABSTAIN

    def gate(self, score: float, engine_verdict: str) -> str:
        """Pass the engine verdict through, or override to INDETERMINATE on abstain."""
        return engine_verdict if self.classify(score) == ACCEPT else ABSTAIN


def _empirical_risk(scores: list[float], correct: list[bool], lam: float, n: int) -> float:
    """Rhat_n(lambda) = (1/n) * sum 1[s_i <= lambda and not correct_i]."""
    acc_wrong = sum(1 for s, c in zip(scores, correct) if s <= lam and not c)
    return acc_wrong / n


def calibrate(scores: list[float], correct: list[bool], alpha: float) -> CalibratedGate:
    """Split-CRC calibration.

    Args:
        scores:  nonconformity scores over the harness-held calibration set.
        correct: whether the engine's verdict was correct for each calibration point.
        alpha:   risk budget in (0, 1).
    Returns:
        CalibratedGate with lambda_hat = the largest accept threshold whose
        finite-sample UCB on the accepted-and-wrong rate is <= alpha.
    """
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    if len(scores) != len(correct):
        raise ValueError("scores and correct must be the same length")
    n = len(scores)
    if n == 0:
        raise ValueError("empty calibration set")

    floor = 1.0 / (n + 1)
    # Candidate thresholds: -inf (accept nothing) plus each observed score.
    # As lambda grows we accept more; risk is monotone non-decreasing, so the
    # feasible region is a lower interval and lambda_hat is its supremum.
    candidates = [-math.inf] + sorted(set(scores))
    lambda_hat = -math.inf
    feasible = False
    for lam in candidates:
        rhat = _empirical_risk(scores, correct, lam, n)
        ucb = (n * rhat + LOSS_BOUND) / (n + 1)
        if ucb <= alpha:
            lambda_hat = lam      # keep the largest feasible threshold
            feasible = True
        else:
            break                 # monotone: once it fails it never recovers

    return CalibratedGate(
        lambda_hat=lambda_hat,
        alpha=alpha,
        n_calibration=n,
        alpha_feasible=feasible,       # False iff even accept-nothing exceeds alpha (alpha < floor)
        finite_sample_floor=floor,
    )


# --------------------------------------------------------------------------- #
# Declared extension points (NOT implemented in v0.1 — honest scoping)
# --------------------------------------------------------------------------- #
def anytime_valid_note() -> str:
    """§8 streaming: fixed-split CRC is valid for a snapshot calibration set only.

    Long-horizon sessions with optional stopping require an anytime-valid variant
    (e-processes / betting martingales, anytime-valid CRC 2026). Set
    VerifierIR.conformal.anytime_valid=true and swap the fixed quantile for a
    time-uniform confidence sequence. Deferred to v0.2.
    """
    return "anytime-valid: deferred to v0.2"


def composition_note() -> str:
    """§8 chained gates: per-gate alpha_i do NOT independently compose to a
    workflow-level guarantee. Declare composition_rule ∈ {independent, pasc_joint,
    bonferroni}; pasc_joint (PASC 2026) gives the pipeline-aware joint-coverage
    bound. v0.1 supports bonferroni (sum of alphas) as the conservative default.
    """
    return "composition: bonferroni (conservative) in v0.1; pasc_joint deferred"
