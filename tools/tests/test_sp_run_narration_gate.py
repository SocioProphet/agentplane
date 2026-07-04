#!/usr/bin/env python3
"""`sp-run narration-gate` CLI — the deployable gate surface, end to end.

Run: python3 -m pytest -q tools/tests/test_sp_run_narration_gate.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.insert(0, _TOOLS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


sp_run = _load("sp_run")
em = _load("trace_cfr_emitter")


def _write(tmp_path, segment, claims):
    segf = tmp_path / "segment.json"
    clf = tmp_path / "claims.json"
    segf.write_text(json.dumps(segment))
    clf.write_text(json.dumps(claims))
    return str(segf), str(clf)


def test_cli_permits_truthful_run(tmp_path, capsys):
    e = em.TraceCfrEmitter("cli-ok")
    e.tool_call("head")
    g1 = e.decision("guard", "true", "pre")
    e.tool_call("body")
    e.decision("guard", "true", "pre")
    e.tool_call("body")
    g3 = e.decision("guard", "false", "pre")
    e.terminal()
    claims = [{"claim_id": "loop", "covers": [g1, g3], "clause": {"primitive": "WHILE"}, "raw": ""}]
    segf, clf = _write(tmp_path, e.seal(), claims)

    rc = sp_run.main(["narration-gate", "--segment", segf, "--claims", clf])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["permitted"] is True and out["gate_verdict"] == "PASS"


def test_cli_denies_lying_run(tmp_path, capsys):
    e = em.TraceCfrEmitter("cli-lie")
    b1 = e.tool_call("body")
    e.decision("guard", "true", "post")
    e.tool_call("body")
    g2 = e.decision("guard", "false", "post")
    e.terminal()
    claims = [{"claim_id": "loop", "covers": [b1, g2], "clause": {"primitive": "WHILE"}, "raw": ""}]
    segf, clf = _write(tmp_path, e.seal(), claims)

    rc = sp_run.main(["narration-gate", "--segment", segf, "--claims", clf])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1                                   # fails closed
    assert out["permitted"] is False and out["gate_verdict"] == "FAIL"
    assert out["unfaithful_claims"] == ["loop"]
    assert "GOV-NARR-STRUCT-001" in out["failure_clusters"]


def test_cli_permits_run_with_no_claims(tmp_path, capsys):
    e = em.TraceCfrEmitter("cli-silent")
    e.tool_call("a")
    e.terminal()
    segf, _ = _write(tmp_path, e.seal(), [])
    rc = sp_run.main(["narration-gate", "--segment", segf])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["permitted"] is True
