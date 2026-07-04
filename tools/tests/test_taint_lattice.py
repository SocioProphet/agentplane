#!/usr/bin/env python3
"""Conformance tests for §11 argument-taint admission (taint_lattice).

Covers: lattice validation (rejects non-lattices), meet/join, integrity taint
propagation, and the CaMeL / lethal-trifecta admission scenario.

Run: python3 -m pytest -q tools/tests/test_taint_lattice.py
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_MOD = os.path.join(_HERE, os.pardir, "taint_lattice.py")
_spec = importlib.util.spec_from_file_location("taint_lattice", _MOD)
tl = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = tl
_spec.loader.exec_module(tl)


def test_integrity_chain_order_and_bounds():
    L = tl.integrity_lattice()
    assert L.leq("UNTRUSTED", "TRUSTED")
    assert L.leq("SANDBOXED", "TRUSTED")
    assert not L.leq("TRUSTED", "UNTRUSTED")
    assert L.leq("TRUSTED", "TRUSTED")            # reflexive
    assert L.meet("TRUSTED", "UNTRUSTED") == "UNTRUSTED"   # glb
    assert L.join("UNTRUSTED", "SANDBOXED") == "SANDBOXED" # lub


def test_diamond_is_a_valid_lattice():
    # top; two incomparable mids a,b; bottom
    L = tl.Lattice(
        elements=["BOT", "A", "B", "TOP"],
        covers=[("BOT", "A"), ("BOT", "B"), ("A", "TOP"), ("B", "TOP")],
    )
    assert L.join("A", "B") == "TOP"
    assert L.meet("A", "B") == "BOT"


def test_non_lattice_rejected():
    # "N" poset: a,b below both c,d with no unique lub for (a,b) -> not a lattice
    with pytest.raises(tl.LatticeError):
        tl.Lattice(
            elements=["a", "b", "c", "d"],
            covers=[("a", "c"), ("a", "d"), ("b", "c"), ("b", "d")],
        )


def test_taint_propagates_to_least_trusted():
    L = tl.integrity_lattice()
    # a value built from trusted config + untrusted web content is UNTRUSTED
    assert L.propagate(["TRUSTED", "UNTRUSTED"]) == "UNTRUSTED"
    assert L.propagate(["TRUSTED", "SANDBOXED"]) == "SANDBOXED"
    assert L.propagate(["TRUSTED", "TRUSTED"]) == "TRUSTED"
    with pytest.raises(tl.LatticeError):
        L.propagate([])


def test_send_email_admission_camel_scenario():
    L = tl.integrity_lattice()
    required = {"recipient": "TRUSTED", "body": "SANDBOXED"}

    # licit: recipient from the user's address book (TRUSTED), body sandboxed
    ok_labels = {"recipient": "TRUSTED", "body": "SANDBOXED"}
    finding, viols = tl.admit(ok_labels, required, L)
    assert finding == tl.FINDING_OK and viols == []

    # attack: recipient derived from untrusted web content (prompt injection)
    bad_labels = {"recipient": L.propagate(["TRUSTED", "UNTRUSTED"]), "body": "SANDBOXED"}
    finding, viols = tl.admit(bad_labels, required, L, origins={"recipient": "web_page_content"})
    assert finding == tl.FINDING_VIOLATION
    assert len(viols) == 1
    v = viols[0]
    assert v.arg_name == "recipient" and v.required == "TRUSTED" and v.actual == "UNTRUSTED"
    assert v.origin == "web_page_content"


def test_missing_provenance_treated_as_least_trusted():
    L = tl.integrity_lattice()
    finding, viols = tl.admit({}, {"recipient": "TRUSTED"}, L)
    assert finding == tl.FINDING_VIOLATION
    assert viols[0].actual == "UNTRUSTED"
