#!/usr/bin/env python3
"""WO_FIBER_005-007 proof-of-algebra: descend / traverse / fiber-product verdict on H.

Proves, against the in-memory H built by fiber_projection (no Rust, no LLM), that the
fibered-retrieval loop is worth its keep:
  * a multi-hop ownership query crosses a fiber boundary and returns a DOUBLY grounded
    answer (both page anchors + a POS verdict with an agreeing witness);
  * a cross-document contradiction yields NEG with a disagreeing witness;
  * no shared claim ⇒ ZERO (vacuous cover); a below-floor extraction ⇒ forced ZERO;
  * an ambiguous descent trips the REAL conformal gate ⇒ INDETERMINATE, not a guessed cite;
  * WallGuard hides a restricted target ⇒ the hop never happens (fail-closed);
  * edge-class purity: traverse ignores E^⊑, descend ignores E_R (INV-F2).

Stdlib + pytest + the real conformal_gate. Run: python3 -m pytest -q tools/tests/test_fiber_retrieval.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    path = os.path.join(_HERE, os.pardir, f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


cg = _load("conformal_gate")
sg = _load("stopgate_artifact")
fp = _load("fiber_projection")
fr = _load("fiber_retrieval")

_WIN = dict(window_start="2026-07-04T00:00:00Z", window_end="2026-07-04T00:00:01Z",
            evaluated_at="2026-07-04T00:00:02Z")

T = "t"
OWNS = "gleif-L2:isDirectParentOf"
CLAIM = "claim:owns_pct:parentco|subco"  # canonical shared claim variable (§3.4.1)


def _node(node_id, kind, display, *, attrs=None, conf=None, anchor=None):
    entry = {
        "graph_node": {
            "node_id": node_id, "tenant_id": T, "node_kind": kind, "display_name": display,
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        }
    }
    if attrs:
        entry["graph_node"]["attributes"] = attrs
    if conf:
        entry["confidentiality_class"] = conf
    if anchor:
        entry["evidence"] = {
            "evidence_id": f"ev-{node_id}", "tenant_id": T, "source_ref": node_id,
            "anchor_ref": anchor, "observed_at": "2026-01-01T00:00:00Z",
            "ingested_at": "2026-07-04T00:00:00Z", "receipt_ref": f"rcpt-{node_id}",
        }
    return entry


def base_fragment(*, parent_pct=100, parent_grade="verified",
                  sub_pct=100, sub_grade="verified", include_sub_claim=True,
                  sub_conf="matter_restricted"):
    parent_attrs = {"claim:owns_pct:parentco|subco": {"value": parent_pct, "egrade": parent_grade}}
    sub_attrs = {}
    if include_sub_claim:
        sub_attrs["claim:owns_pct:parentco|subco"] = {"value": sub_pct, "egrade": sub_grade}
    return {
        "tenant_id": T,
        "nodes": [
            _node("filing-A/root", "document", "ParentCo 10-K", conf="public"),
            _node("filing-A/s4.2", "clause", "Item 4.2", conf="firm_approved"),
            _node("entity/parentco", "organization", "ParentCo Inc.",
                  attrs=parent_attrs, conf="firm_approved", anchor="filing-A#p87§4.2"),
            _node("filing-B/root", "document", "SubCo 10-K", conf="client_confidential"),
            _node("filing-B/s2.1", "clause", "Item 2.1", conf="client_confidential"),
            _node("entity/subco", "organization", "SubCo LLC",
                  attrs=sub_attrs, conf=sub_conf, anchor="filing-B#p14§2.1"),
        ],
        "edges": [
            {"class": "containment", "parent": "filing-A/root", "child": "filing-A/s4.2"},
            {"class": "containment", "parent": "filing-A/s4.2", "child": "entity/parentco"},
            {"class": "containment", "parent": "filing-B/root", "child": "filing-B/s2.1"},
            {"class": "containment", "parent": "filing-B/s2.1", "child": "entity/subco"},
            {"class": "relational", "type_name": OWNS, "src": "entity/parentco", "dst": "entity/subco"},
        ],
    }


def _atoms(g):
    return {k[1]: v for k, v in g.id_map.items()}


def confident_gate():
    """Real split-CRC gate: low scores accept, high scores abstain. λ̂ ≈ 0.49 at α=0.10."""
    scores = [i / 100 for i in range(100)]
    correct = [s <= 0.4 for s in scores]
    return fr.calibrate_gate(scores, correct, alpha=0.10)


# --------------------------------------------------------------------------- #
def test_gate_is_the_real_crc_gate():
    gate = confident_gate()
    assert gate.classify(0.1) == cg.ACCEPT
    assert gate.classify(0.9) == cg.ABSTAIN


def test_pos_ownership_end_to_end_doubly_grounded():
    g = fp.project(base_fragment())
    a = _atoms(g)
    res = fr.retrieve_edge(
        g, a["entity/parentco"], OWNS,
        scorer=fr.scored_walk({}, default=0.1), gate=confident_gate(), query="who does ParentCo control?",
    )
    assert res.verdict == fr.POS
    assert res.egrade == "verified"
    assert res.answer == a["entity/subco"]
    assert res.citations == ["filing-A#p87§4.2", "filing-B#p14§2.1"]
    assert res.witness == {"agree": [("owns_pct:parentco|subco", 100)]}
    assert res.doubly_grounded  # §6.3: both a page anchor AND a non-ZERO verdict
    # the Episode carries BOTH citation types (unsigned — WO_FIBER_007 seals it)
    assert res.episode["Artifact"] == ["filing-A#p87§4.2", "filing-B#p14§2.1"]
    assert res.episode["Claim"] == (OWNS, a["entity/parentco"], a["entity/subco"])


def test_neg_cross_document_contradiction_has_witness():
    g = fp.project(base_fragment(sub_pct=60))  # SubCo's filing disagrees on the %
    a = _atoms(g)
    res = fr.retrieve_edge(
        g, a["entity/parentco"], OWNS,
        scorer=fr.scored_walk({}, default=0.1), gate=confident_gate(), query="q",
    )
    assert res.verdict == fr.NEG
    assert res.witness == {"disagree": [("owns_pct:parentco|subco", 100, 60)]}
    assert res.doubly_grounded  # a contradiction is still a grounded finding


def test_zero_when_no_shared_claim():
    g = fp.project(base_fragment(include_sub_claim=False))
    a = _atoms(g)
    v, w, e = fr.glue_verdict(g, a["entity/parentco"], a["entity/subco"])
    assert (v, w) == (fr.ZERO, None)  # vacuous cover, witnessless


def test_forced_zero_below_extraction_floor():
    g = fp.project(base_fragment(sub_grade="sampled"))
    a = _atoms(g)
    # with E_floor=verified, SubCo's sampled claim is below the floor ⇒ no test possible
    v, w, _e = fr.glue_verdict(g, a["entity/parentco"], a["entity/subco"], e_floor="verified")
    assert (v, w) == (fr.ZERO, None)
    # but at E_floor=sampled it becomes testable again (and agrees → POS)
    v2, _w, _e = fr.glue_verdict(g, a["entity/parentco"], a["entity/subco"], e_floor="sampled")
    assert v2 == fr.POS


def test_conformal_abstention_yields_indeterminate_not_a_guess():
    g = fp.project(base_fragment())
    a = _atoms(g)
    # make the descent into SubCo's fiber ambiguous: its section scores above λ̂.
    scorer = fr.scored_walk({a["filing-B/s2.1"]: 0.9}, default=0.1)
    res = fr.retrieve_edge(g, a["entity/parentco"], OWNS,
                           scorer=scorer, gate=confident_gate(), query="q")
    assert res.verdict == fr.INDETERMINATE          # abstained, distinct from ZERO
    assert not res.doubly_grounded                  # no confident citation was produced
    assert res.citations == []


def test_wallguard_hides_restricted_target():
    g = fp.project(base_fragment())  # SubCo is matter_restricted
    a = _atoms(g)
    cleared = fr.label_gate({"firm_approved", "public"})  # SubCo NOT cleared
    res = fr.retrieve_edge(g, a["entity/parentco"], OWNS,
                           scorer=fr.scored_walk({}, default=0.1), gate=confident_gate(),
                           query="q", visible=cleared)
    assert res.verdict == fr.ZERO                   # the hop never happened
    assert res.answer is None


def _pos_result(g, a):
    return fr.retrieve_edge(g, a["entity/parentco"], OWNS,
                            scorer=fr.scored_walk({}, default=0.1), gate=confident_gate(), query="q")


def _signer():
    return sg.Signer.from_seed(b"\x02" * 32, "fiber-test-key")


def test_seal_pos_signs_pass_permit_and_independently_verifies():
    g = fp.project(base_fragment())
    a = _atoms(g)
    artifact, disposition = fr.seal_episode(
        _pos_result(g, a), signer=_signer(), session_id="s1", workcell_id="w1", **_WIN)
    assert artifact["verdict"] == sg.VERDICT_PASS
    assert disposition == "permit"
    assert artifact["evaluated_by"]["kind"] == sg.HARNESS_KIND  # model excluded from sealing (§5.1)
    assert artifact["native_verdict"] == fr.POS
    assert artifact["evidence_grade"] == "verified"
    assert artifact["fiber_episode"]["Claim"][0] == OWNS
    # both page anchors became semantic-layer evidence (so PASS is layer-bound, §5.3)
    assert {e["source_event_uuid"] for e in artifact["evidence"]} == {
        "filing-A#p87§4.2", "filing-B#p14§2.1"}
    # independently verifiable from the artifact + public key alone
    keyring = sg.Keyring().add_signer(_signer())
    assert sg.verify_artifact(artifact, keyring).ok


def test_seal_neg_is_fail_deny():
    g = fp.project(base_fragment(sub_pct=60))
    a = _atoms(g)
    artifact, disposition = fr.seal_episode(
        _pos_result(g, a), signer=_signer(), session_id="s1", workcell_id="w1", **_WIN)
    assert artifact["verdict"] == sg.VERDICT_FAIL
    assert disposition == "deny"
    assert artifact["native_verdict"] == fr.NEG
    assert artifact["verdict"] not in sg.PERMIT_ELIGIBLE


def test_seal_wallguard_zero_is_no_permit():
    g = fp.project(base_fragment())
    a = _atoms(g)
    res = fr.retrieve_edge(g, a["entity/parentco"], OWNS,
                           scorer=fr.scored_walk({}, default=0.1), gate=confident_gate(),
                           query="q", visible=fr.label_gate({"firm_approved", "public"}))
    artifact, disposition = fr.seal_episode(
        res, signer=_signer(), session_id="s1", workcell_id="w1", **_WIN)
    assert artifact["verdict"] == sg.VERDICT_INDETERMINATE
    assert disposition == "deny-require-override"
    assert artifact["verdict"] not in sg.PERMIT_ELIGIBLE


def test_tampered_seal_fails_verification():
    g = fp.project(base_fragment())
    a = _atoms(g)
    artifact, _ = fr.seal_episode(
        _pos_result(g, a), signer=_signer(), session_id="s1", workcell_id="w1", **_WIN)
    keyring = sg.Keyring().add_signer(_signer())
    assert sg.verify_artifact(artifact, keyring).ok
    # flip the answer after signing → the signature no longer covers the bytes → permit dies
    tampered = {**artifact, "subject": ["entity/evil"]}
    assert not sg.verify_artifact(tampered, keyring).ok


def test_inv_f2_edge_class_purity():
    g = fp.project(base_fragment())
    a = _atoms(g)
    # traverse follows ONLY E_R: asking it to walk the containment type finds nothing.
    assert fr.traverse(g, [a["filing-A/root"]], "contains", beam_k=8) == []
    # relational neighbour exists under the real relational type.
    assert fr.relational_neighbors(g, a["entity/parentco"], OWNS) == [a["entity/subco"]]
    # descend follows ONLY E^⊑: the relational target is never a containment child.
    assert a["entity/subco"] not in fr.containment_children(g, a["entity/parentco"])
    assert fr.containment_children(g, a["filing-A/s4.2"]) == [a["entity/parentco"]]
