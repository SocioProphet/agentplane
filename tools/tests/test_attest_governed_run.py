#!/usr/bin/env python3
"""Governed-run narration attestation: core + `sp-run attest-run` CLI.

Run: python3 -m pytest -q tools/tests/test_attest_governed_run.py
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


att = _load("attest_governed_run")
br = _load("trace_cfr_reasoning_bridge")
sg = _load("stopgate_artifact")
sp_run = _load("sp_run")

_ATT_SCHEMA = V(json.load(open(os.path.join(_ROOT, "schemas", "trace-cfr-run-attestation.schema.v0.1.json"))))


def _ev(eid, etype, **cf):
    e = {"id": eid, "type": "ReasoningEvent", "specVersion": "2.0.0", "runRef": "run1",
         "eventType": etype, "summary": "", "traceLevel": "workspace-safe",
         "trustLevel": "trusted-control-input", "capturedAt": "2026-07-04T00:00:00Z"}
    if cf:
        e["controlFlow"] = cf
    return e


def _dowhile_events():
    return [
        _ev("e1", "reasoning.tool.called", site="body"),
        _ev("e2", "reasoning.decision.branched", site="guard", branch_taken="true", guard_position="post"),
        _ev("e3", "reasoning.tool.called", site="body"),
        _ev("e4", "reasoning.decision.branched", site="guard", branch_taken="false", guard_position="post"),
        _ev("e5", "reasoning.run.completed", site="exit"),
    ]


def _covers(events, session):
    seg = br.reasoning_events_to_segment(events, session_id=session)
    return [seg["events"][0]["event_id"], seg["events"][-1]["event_id"]]


def _signer():
    return sg.Signer.from_seed(b"\x05" * 32, "harness-k")


def test_attest_truthful_run_permits_and_is_schema_valid():
    events = _dowhile_events()
    claims = [{"claim_id": "loop", "covers": _covers(events, "run1"), "clause": {"primitive": "DO_WHILE"}}]
    attestation, report = att.attest_run(events, claims, _signer(), session_id="run1")
    assert report.permitted and report.gate_verdict == "PASS"
    assert list(_ATT_SCHEMA.iter_errors(attestation)) == []


def test_attest_lying_run_fails_closed():
    events = _dowhile_events()
    claims = [{"claim_id": "loop", "covers": _covers(events, "run1"), "clause": {"primitive": "WHILE"}}]
    _, report = att.attest_run(events, claims, _signer(), session_id="run1")
    assert not report.permitted and report.gate_verdict == "FAIL"


def test_write_attestation_binds_into_evidence_folder(tmp_path):
    events = _dowhile_events()
    attestation, _ = att.attest_run(events, [], _signer(), session_id="run1")
    p = att.write_attestation(attestation, tmp_path / "run" / "attempts" / "001")
    assert p.name == "narration-fidelity-attestation.json" and p.exists()
    assert json.loads(p.read_text())["artifact_kind"] == "trace_cfr_run_attestation"


def test_cli_attest_run_writes_into_run_dir(tmp_path, capsys):
    events = _dowhile_events()
    covers = _covers(events, "cli-run")
    evf = tmp_path / "events.json"
    clf = tmp_path / "claims.json"
    rundir = tmp_path / "evidence"
    evf.write_text(json.dumps(events))
    clf.write_text(json.dumps([{"claim_id": "loop", "covers": covers, "clause": {"primitive": "WHILE"}}]))

    rc = sp_run.main(["attest-run", "--events", str(evf), "--claims", str(clf),
                      "--run-dir", str(rundir), "--session-id", "cli-run"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["gate_verdict"] == "FAIL"          # lying claim -> fails closed
    written = rundir / "narration-fidelity-attestation.json"
    assert written.exists() and out["attestation_written"] == str(written)
    assert list(_ATT_SCHEMA.iter_errors(json.loads(written.read_text()))) == []
