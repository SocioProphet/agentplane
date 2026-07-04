#!/usr/bin/env python3
"""Run-level signed attestation (SP-TRACE-CFR §5) + CLI --out.

Run: python3 -m pytest -q tools/tests/test_trace_cfr_run_attestation.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

from jsonschema.validators import Draft202012Validator as V

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
_ROOT = os.path.join(_TOOLS, os.pardir)
sys.path.insert(0, _TOOLS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


rt = _load("trace_cfr_runtime")
sg = _load("stopgate_artifact")
em = _load("trace_cfr_emitter")
sp_run = _load("sp_run")

_SCHEMA = V(json.load(open(os.path.join(_ROOT, "schemas", "trace-cfr-run-attestation.schema.v0.1.json"))))


def _signer():
    return sg.Signer.from_seed(b"\x09" * 32, key_id="harness-k")


def _lying_run(session="att-lie"):
    r = rt.RunRecorder(session, signer=_signer())
    b1 = r.tool_call("body")
    r.decision("guard", "true", "post")
    r.tool_call("body")
    g2 = r.decision("guard", "false", "post")
    r.terminal()
    r.narrate("loop", "WHILE", covers=[b1, g2])
    return r


def test_attestation_is_schema_valid_and_signature_verifies():
    rep = _lying_run().finish()
    att = rt.build_run_attestation(rep, _signer(), session_id="att-lie")
    assert list(_SCHEMA.iter_errors(att)) == []
    ok, problems = rt.verify_run_attestation(att, sg.Keyring().add_signer(_signer()))
    assert ok, problems
    assert att["gate_verdict"] == "FAIL"
    assert att["verdicts"]["NEG"] == 1
    assert "GOV-NARR-STRUCT-001" in att["anomalies"]
    assert att["segment_ref"]["segment_hash"].startswith("sha256:")


def test_tampered_attestation_fails_verification():
    rep = _lying_run().finish()
    att = rt.build_run_attestation(rep, _signer(), session_id="att-lie")
    att["gate_verdict"] = "PASS"   # forge a permit after signing
    ok, problems = rt.verify_run_attestation(att, sg.Keyring().add_signer(_signer()))
    assert not ok and any("signature" in p for p in problems)


def test_model_authored_attestation_rejected():
    rep = _lying_run().finish()
    att = rt.build_run_attestation(rep, _signer(), session_id="att-lie")
    att["evaluated_by"] = {"kind": "model"}
    ok, problems = rt.verify_run_attestation(att, sg.Keyring().add_signer(_signer()))
    assert not ok and any("model-exclusion" in p for p in problems)


def test_cli_out_writes_valid_attestation(tmp_path, capsys):
    e = em.TraceCfrEmitter("cli-att")
    b1 = e.tool_call("body")
    e.decision("guard", "true", "post")
    e.tool_call("body")
    g2 = e.decision("guard", "false", "post")
    e.terminal()
    seg = e.seal()
    segf = tmp_path / "seg.json"
    clf = tmp_path / "claims.json"
    outf = tmp_path / "attestation.json"
    segf.write_text(json.dumps(seg))
    clf.write_text(json.dumps([{"claim_id": "loop", "covers": [b1, g2], "clause": {"primitive": "WHILE"}}]))

    rc = sp_run.main(["narration-gate", "--segment", str(segf), "--claims", str(clf),
                      "--session-id", "cli-att", "--out", str(outf)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["attestation_written"] == str(outf)
    att = json.loads(outf.read_text())
    assert list(_SCHEMA.iter_errors(att)) == []
    assert att["session_id"] == "cli-att" and att["gate_verdict"] == "FAIL"
    assert att["segment_ref"]["segment_hash"] == seg["segment"]["segment_hash"]
