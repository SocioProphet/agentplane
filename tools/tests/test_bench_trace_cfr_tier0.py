#!/usr/bin/env python3
"""Tier-0 latency acceptance (SPEC §6): p95 < 50ms on segments <= 2,000 events.

Run: python3 -m pytest -q tools/tests/test_bench_trace_cfr_tier0.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, _TOOLS)

spec = importlib.util.spec_from_file_location("bench_trace_cfr_tier0", os.path.join(_TOOLS, "bench_trace_cfr_tier0.py"))
bench = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bench
spec.loader.exec_module(bench)


def test_tier0_p95_under_budget_at_2000_events():
    rows = bench.bench(sizes=(2000,), runs=20)
    size, n_events, p50, p95 = rows[0]
    assert n_events <= 2000
    assert p95 < 50.0, f"Tier-0 p95={p95:.2f}ms exceeds 50ms budget (p50={p50:.2f})"


def test_scaling_is_near_linear_not_quadratic():
    # guards against a regression to the old superlinear dominators (which hung at 2000)
    rows = {size: p95 for size, _n, _p50, p95 in bench.bench(sizes=(500, 2000), runs=10)}
    # 4x the events should cost well under 16x (quadratic) the time; allow generous slack
    assert rows[2000] < rows[500] * 10, rows
