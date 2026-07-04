#!/usr/bin/env python3
"""Tier-0 latency benchmark for SP-TRACE-CFR (SPEC §6 acceptance criterion).

Measures the p95 wall time of the Tier-0 path — P0 ingest -> P1 CFG -> P2 normalize
-> R_H hammock — on segments up to 2,000 events. Acceptance: p95 < 50 ms.

Fixture-generation (emit/seal) is EXCLUDED from timing; only the recovery path is
measured, starting from raw JSONL bytes as ingest sees them. Stdlib-only.
Run: python3 tools/bench_trace_cfr_tier0.py
"""

from __future__ import annotations

import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recover_hammock as rh  # noqa: E402
import trace_cfr_cfg as cfg  # noqa: E402
import trace_cfr_emitter as em  # noqa: E402
import trace_cfr_ingest as ing  # noqa: E402
import trace_cfr_normalize as norm  # noqa: E402


def make_segment(n_events: int):
    """A realistic mixed program: long SEQ runs with periodic loops and a sidechain,
    folded so node count tracks event count up to n_events."""
    e = em.TraceCfrEmitter(f"bench-{n_events}")
    i = 0
    while i < n_events - 4:
        e.tool_call(f"t{i}")
        i += 1
        if i % 50 == 0 and i < n_events - 8:  # periodic small loop (2 iterations)
            e.decision(f"g{i}", "true", "pre")
            e.tool_call(f"b{i}")
            e.decision(f"g{i}", "false", "pre")
            i += 3
    with e.sidechain("delegate", "sc"):
        e.tool_call("sub")
    e.terminal()
    return e.to_jsonl(), e.seal()["segment"]["segment_hash"]


def tier0(raw: bytes, expected_hash: str):
    r = ing.ingest(raw, expected_hash=expected_hash)      # P0
    if not r.ok:
        raise RuntimeError(r.reasons)
    g = cfg.build_cfg(r.events)                            # P1
    n = norm.normalize(g)                                  # P2
    return rh.recover_hammock(g, n)                        # R_H


def bench(sizes=(100, 500, 1000, 2000), runs=30):
    rows = []
    for size in sizes:
        raw, h = make_segment(size)
        n_events = raw.count(b"\n")
        # warm up
        tier0(raw, h)
        samples = []
        for _ in range(runs):
            t0 = time.perf_counter()
            tier0(raw, h)
            samples.append((time.perf_counter() - t0) * 1000.0)
        samples.sort()
        p50 = statistics.median(samples)
        p95 = samples[min(len(samples) - 1, int(0.95 * len(samples)))]
        rows.append((size, n_events, p50, p95))
    return rows


if __name__ == "__main__":
    rows = bench()
    print(f"  {'target':>7} {'events':>7} {'p50 ms':>9} {'p95 ms':>9}  budget=50ms")
    worst = 0.0
    for size, n_events, p50, p95 in rows:
        worst = max(worst, p95 if n_events <= 2000 else 0.0)
        flag = "" if p95 < 50 else "  <-- OVER"
        print(f"  {size:>7} {n_events:>7} {p50:>9.2f} {p95:>9.2f}{flag}")
    print("  " + "-" * 44)
    ok = worst < 50.0
    print(f"  Tier-0 p95 (<=2000 events): {worst:.2f} ms  -> {'PASS' if ok else 'FAIL'} (<50ms)")
    sys.exit(0 if ok else 1)
