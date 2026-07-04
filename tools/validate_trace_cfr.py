#!/usr/bin/env python3
"""Validator CLI for SP-TRACE-CFR (repo `validate-*` convention).

Checks: the trace-cfr-segment schema is a valid Draft-2020 schema; a self-test
segment emitted by the reference emitter conforms to it and recovers through the
full pipeline; and the SP-EVAL-TRACE-CFR acceptance criteria all pass.

Exit 0 on success, 1 on any problem. Run: python3 tools/validate_trace_cfr.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema.validators import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import eval_trace_cfr as ev  # noqa: E402
import recover_hammock as rh  # noqa: E402
import trace_cfr_cfg as cfg  # noqa: E402
import trace_cfr_emitter as em  # noqa: E402
import trace_cfr_ingest as ing  # noqa: E402
import trace_cfr_normalize as norm  # noqa: E402

SEG_SCHEMA = ROOT / "schemas" / "trace-cfr-segment.schema.v0.1.json"


def _schema() -> dict:
    d = json.loads(SEG_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(d)
    return d


def _self_test(schema: dict) -> list[str]:
    problems: list[str] = []
    e = em.TraceCfrEmitter("validate")
    e.tool_call("read")
    with e.sidechain("delegate", "sc"):
        e.tool_call("sub")
    e.terminal()
    seg = e.seal()
    errs = list(Draft202012Validator(schema).iter_errors(seg))
    if errs:
        problems.append(f"segment fails schema: {errs[0].message}")
    r = ing.ingest_sealed_segment(seg)
    if not r.ok:
        problems.append(f"ingest rejected a valid segment: {r.reasons}")
        return problems
    g = cfg.build_cfg(r.events)
    rec = rh.recover_hammock(g, norm.normalize(g))
    if "SPAWN_JOIN" not in rec.primitives():
        problems.append("R_H failed to recover SPAWN_JOIN from the self-test segment")
    return problems


def main() -> int:
    problems: list[str] = []
    schema = _schema()
    problems += _self_test(schema)
    report = ev.evaluate()
    problems += [f"acceptance criterion failed: {k}" for k, v in ev.acceptance(report).items() if not v]

    if problems:
        print("TRACE-CFR VALIDATION FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("trace-cfr: segment schema valid, self-test OK, SP-EVAL acceptance PASS")
    print(f"  (S8 lie-recall={report['S8_neg_recall']:.2f}, S5 GOV-IRRED fp={report['S5_fp']}, "
          f"AC gap={report['AC_gap']}; Tier-0 latency via `make test`/bench)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
