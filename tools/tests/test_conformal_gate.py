#!/usr/bin/env python3
"""§14.5 conformal-coverage conformance obligation for conformal_gate.

Proves the split-CRC guarantee on synthetic data: the accepted-and-wrong rate on
a held-out test set is <= alpha (+ finite-sample slack), across many trials; that
abstention actually occurs; and that lambda_hat is monotone in alpha.

Stdlib + pytest. Run: python3 -m pytest -q tools/tests/test_conformal_gate.py
"""

from __future__ import annotations

import importlib.util
import math
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_MOD = os.path.join(_HERE, os.pardir, "conformal_gate.py")
_spec = importlib.util.spec_from_file_location("conformal_gate", _MOD)
cg = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cg  # register before exec so @dataclass can resolve its module
_spec.loader.exec_module(cg)


def _synth(n, rng):
    """Higher score => more likely wrong. score ~ U(0,1); P(correct) = 1 - score."""
    scores = [rng.random() for _ in range(n)]
    correct = [rng.random() < (1.0 - s) for s in scores]
    return scores, correct


def test_marginal_coverage_holds_in_expectation():
    """CRC controls E[accept AND wrong] <= alpha. We estimate that expectation by
    Monte Carlo over many (calibration, test) draws and assert the mean is bounded.
    Per-trial excursions above alpha are expected and NOT a violation — the guarantee
    is marginal, not conditional/per-trial."""
    alpha = 0.10
    n_cal, n_test, trials = 500, 4000, 80
    total_accept_wrong = 0
    total_test = 0
    abstained_every_trial = True
    for seed in range(trials):
        rng = random.Random(1000 + seed)
        cal_s, cal_c = _synth(n_cal, rng)
        gate = cg.calibrate(cal_s, cal_c, alpha)
        test_s, test_c = _synth(n_test, rng)
        total_accept_wrong += sum(
            1 for s, c in zip(test_s, test_c) if gate.classify(s) == cg.ACCEPT and not c
        )
        total_test += n_test
        if gate.lambda_hat >= max(test_s):
            abstained_every_trial = False
    mean_rate = total_accept_wrong / total_test
    # Monte-Carlo slack on the pooled estimate of E[L]
    mc_slack = 3.0 * math.sqrt(alpha * (1 - alpha) / total_test)
    assert mean_rate <= alpha + mc_slack, f"E[accept & wrong]={mean_rate:.4f} > {alpha}+{mc_slack:.4f}"
    # sanity: not vacuously conservative (it isn't abstaining on everything)
    assert mean_rate > 0.3 * alpha, f"gate is over-conservative: mean_rate={mean_rate:.4f}"
    # with alpha=0.1 and this DGP, abstention must engage in every trial
    assert abstained_every_trial


def test_lambda_monotone_in_alpha():
    rng = random.Random(7)
    cal_s, cal_c = _synth(800, rng)
    lambdas = [cg.calibrate(cal_s, cal_c, a).lambda_hat for a in (0.02, 0.05, 0.10, 0.20, 0.40)]
    # larger risk budget => accept more => larger (or equal) threshold
    assert all(lambdas[i] <= lambdas[i + 1] for i in range(len(lambdas) - 1)), lambdas


def test_alpha_below_finite_sample_floor_abstains_all():
    rng = random.Random(3)
    cal_s, cal_c = _synth(9, rng)          # n=9 => floor = 1/10 = 0.1
    gate = cg.calibrate(cal_s, cal_c, alpha=0.05)  # below floor
    assert gate.alpha_feasible is False
    assert gate.lambda_hat == -math.inf
    # abstains on everything, including the smallest possible score
    assert gate.classify(-1e9) == cg.ABSTAIN


def test_gate_passthrough_and_override():
    rng = random.Random(11)
    cal_s, cal_c = _synth(400, rng)
    gate = cg.calibrate(cal_s, cal_c, alpha=0.15)
    # a very low score (confident) accepts -> passes engine verdict through
    assert gate.gate(-1e9, "VIOLATION") == "VIOLATION"
    # a maximal score (unrecoverable) abstains -> INDETERMINATE
    assert gate.gate(1e9, "VIOLATION") == cg.ABSTAIN


def test_input_validation():
    import pytest

    with pytest.raises(ValueError):
        cg.calibrate([0.1], [True], alpha=0.0)
    with pytest.raises(ValueError):
        cg.calibrate([0.1, 0.2], [True], alpha=0.1)  # length mismatch
    with pytest.raises(ValueError):
        cg.calibrate([], [], alpha=0.1)
