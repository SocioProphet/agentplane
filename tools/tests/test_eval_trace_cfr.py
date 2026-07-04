#!/usr/bin/env python3
"""SP-EVAL-TRACE-CFR-001 acceptance gate (SPEC §6) as a CI test.

Run: python3 -m pytest -q tools/tests/test_eval_trace_cfr.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, _TOOLS)

spec = importlib.util.spec_from_file_location("eval_trace_cfr", os.path.join(_TOOLS, "eval_trace_cfr.py"))
ev = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ev
spec.loader.exec_module(ev)

_REPORT = ev.evaluate()
_ACC = ev.acceptance(_REPORT)


def test_all_acceptance_criteria_pass():
    failing = [k for k, v in _ACC.items() if not v]
    assert not failing, f"failing acceptance criteria: {failing}\nreport={_REPORT}"


def test_no_false_accusations_release_blockers():
    # S4 (threaded truthful) and S8z (zero-trip) NEG counts are hard release blockers
    assert _REPORT["S4_neg"] == 0
    assert _REPORT["S8z_neg"] == 0


def test_lies_are_caught():
    assert _REPORT["S8_neg_recall"] >= 0.95


def test_latent_never_positive():
    assert _REPORT["S7_pos"] == 0


def test_govirred_zero_false_positive():
    assert _REPORT["S5_fp"] == 0
    assert _REPORT["S5_recall"] >= 0.9


def test_abstention_calibration_separates():
    # undecidable strata abstain more than decidable ones (the moat metric)
    assert _REPORT["AC_gap"] > 0
