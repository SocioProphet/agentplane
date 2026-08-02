#!/usr/bin/env python3
"""Coverage for the CHRONOS carrier passthrough extension to the sociosphere bridge.

This is additive coverage alongside tests/test_sourceos_binding_projection.py:
same three modules (validate_bundle, emit_run_artifact, emit_replay_artifact),
same bridge, a second carried-object type. See docs/sociosphere-bridge.md
("CHRONOS carrier passthrough") and issue #329.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "chronos-carrier"
sys.path.insert(0, str(SCRIPTS))

import emit_replay_artifact  # noqa: E402
import emit_run_artifact  # noqa: E402
import validate_bundle  # noqa: E402

VALID_CARRIER = {
    "sourceEvidenceRef": "urn:chronos:evidence:neurasp-adjudication-0007",
    "methodFamily": "neurasp-adjudication",
    "claimStatus": "proposed",
    "validationStatus": "unvalidated",
    "nonAuthorityDeclaration": True,
    "owningPlane": "ontogenesis",
    "replayRef": "urn:chronos:replay:neurasp-adjudication-0007",
}

# SourceOS binding fixture reused verbatim from test_sourceos_binding_projection.py
# to prove the two carried-object types coexist without interference.
SOURCEOS_BINDING = {
    "contentSpecRef": "urn:srcos:content-spec:sourceos-workstation",
    "evidenceBundleRef": "urn:srcos:evidence-bundle:sourceos-workstation-dev-0001",
}


class ChronosCarrierGateTests(unittest.TestCase):
    """scripts/validate_bundle.py's fail-closed structural gate."""

    def test_absent_carrier_is_not_applicable(self) -> None:
        result = validate_bundle.validate_chronos_carrier({})
        self.assertEqual(result, {"enabled": False, "result": "not_applicable"})

    def test_valid_carrier_passes_and_projects_fields(self) -> None:
        spec = {"chronosCarrier": dict(VALID_CARRIER)}
        result = validate_bundle.validate_chronos_carrier(spec)
        self.assertEqual(result["enabled"], True)
        self.assertEqual(result["result"], "pass")
        for key, value in VALID_CARRIER.items():
            self.assertEqual(result[key], value)

    def test_missing_required_field_rejected(self) -> None:
        for missing_key in validate_bundle.CHRONOS_CARRIER_REQUIRED_KEYS:
            carrier = dict(VALID_CARRIER)
            del carrier[missing_key]
            spec = {"chronosCarrier": carrier}
            with self.assertRaises(SystemExit, msg=f"expected rejection when {missing_key} is missing"):
                validate_bundle.validate_chronos_carrier(spec)

    def test_non_authority_declaration_false_rejected(self) -> None:
        """An improperly-authorized carrier: it does not disclaim agentplane authority."""
        carrier = dict(VALID_CARRIER)
        carrier["nonAuthorityDeclaration"] = False
        spec = {"chronosCarrier": carrier}
        with self.assertRaises(SystemExit):
            validate_bundle.validate_chronos_carrier(spec)

    def test_owning_plane_agentplane_rejected(self) -> None:
        """An improperly-authorized carrier: it tries to route canonical ownership through agentplane."""
        carrier = dict(VALID_CARRIER)
        carrier["owningPlane"] = "agentplane"
        spec = {"chronosCarrier": carrier}
        with self.assertRaises(SystemExit):
            validate_bundle.validate_chronos_carrier(spec)

    def test_owning_plane_agentplane_case_insensitive_rejected(self) -> None:
        carrier = dict(VALID_CARRIER)
        carrier["owningPlane"] = "AgentPlane"
        spec = {"chronosCarrier": carrier}
        with self.assertRaises(SystemExit):
            validate_bundle.validate_chronos_carrier(spec)

    def test_non_string_method_family_rejected(self) -> None:
        carrier = dict(VALID_CARRIER)
        carrier["methodFamily"] = 12345
        spec = {"chronosCarrier": carrier}
        with self.assertRaises(SystemExit):
            validate_bundle.validate_chronos_carrier(spec)


class ChronosCarrierEmitProjectionTests(unittest.TestCase):
    """scripts/emit_run_artifact.py and scripts/emit_replay_artifact.py permissive projection."""

    def test_valid_carrier_projects_consistently_across_emitters(self) -> None:
        spec = {"chronosCarrier": dict(VALID_CARRIER)}

        self.assertEqual(emit_run_artifact.extract_chronos_carrier(spec), VALID_CARRIER)
        self.assertEqual(emit_replay_artifact.extract_chronos_carrier(spec), VALID_CARRIER)

    def test_empty_carrier_projects_to_empty_object(self) -> None:
        spec: dict = {}

        self.assertEqual(emit_run_artifact.extract_chronos_carrier(spec), {})
        self.assertEqual(emit_replay_artifact.extract_chronos_carrier(spec), {})

    def test_emitters_do_not_fail_closed(self) -> None:
        """The fail-closed gate lives only in validate_bundle; emitters just record facts,
        matching the existing extract_sourceos_image_production permissive-collector pattern."""
        carrier = dict(VALID_CARRIER)
        del carrier["nonAuthorityDeclaration"]
        spec = {"chronosCarrier": carrier}

        # Must not raise, unlike validate_bundle.validate_chronos_carrier on the same input.
        run_projection = emit_run_artifact.extract_chronos_carrier(spec)
        replay_projection = emit_replay_artifact.extract_chronos_carrier(spec)
        self.assertEqual(run_projection["methodFamily"], VALID_CARRIER["methodFamily"])
        self.assertEqual(replay_projection["methodFamily"], VALID_CARRIER["methodFamily"])


class SupersetTests(unittest.TestCase):
    """Confirm the widened bridge still carries the pre-existing artifact type unchanged."""

    def test_sourceos_binding_and_chronos_carrier_coexist(self) -> None:
        spec = {
            "integrationRefs": {"sourceos": dict(SOURCEOS_BINDING)},
            "chronosCarrier": dict(VALID_CARRIER),
        }

        # Pre-existing SourceOS projection is untouched by the new carrier field.
        self.assertEqual(validate_bundle.extract_sourceos_bindings(spec), SOURCEOS_BINDING)
        self.assertEqual(emit_run_artifact.extract_sourceos_bindings(spec), SOURCEOS_BINDING)
        self.assertEqual(emit_replay_artifact.extract_sourceos_bindings(spec), SOURCEOS_BINDING)

        # New CHRONOS carrier projection is present alongside it.
        gate = validate_bundle.validate_chronos_carrier(spec)
        self.assertEqual(gate["result"], "pass")
        self.assertEqual(emit_run_artifact.extract_chronos_carrier(spec), VALID_CARRIER)
        self.assertEqual(emit_replay_artifact.extract_chronos_carrier(spec), VALID_CARRIER)

    def test_bundle_with_only_sourceos_binding_has_not_applicable_chronos_gate(self) -> None:
        spec = {"integrationRefs": {"sourceos": dict(SOURCEOS_BINDING)}}

        gate = validate_bundle.validate_chronos_carrier(spec)
        self.assertEqual(gate, {"enabled": False, "result": "not_applicable"})
        self.assertEqual(emit_run_artifact.extract_chronos_carrier(spec), {})
        self.assertEqual(emit_replay_artifact.extract_chronos_carrier(spec), {})


class ChronosCarrierCliFixtureTests(unittest.TestCase):
    """End-to-end CLI coverage: scripts/validate_bundle.py against full Bundle fixtures,
    following this repo's valid.*/reject.* fixture convention (see e.g.
    tests/fixtures/reviews/, Makefile's `!`-prefixed negative-case targets)."""

    def _run_validate(self, fixture_name: str) -> subprocess.CompletedProcess:
        fixture = FIXTURES / fixture_name
        self.assertTrue(fixture.exists(), f"missing fixture: {fixture}")
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_bundle.py"), str(fixture)],
            capture_output=True,
            text=True,
        )

    def test_valid_chronos_carrier_bundle_passes(self) -> None:
        result = self._run_validate("valid.chronos-carrier-bundle.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[validate] OK", result.stdout)

    def test_reject_non_authority_declaration_false(self) -> None:
        """Improperly-authorized carrier: does not disclaim agentplane authority."""
        result = self._run_validate("reject.chronos-carrier-bundle.non-authority-declaration-false.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("nonAuthorityDeclaration must be true", result.stderr)

    def test_reject_owning_plane_agentplane(self) -> None:
        """Improperly-authorized carrier: routes canonical ownership through agentplane."""
        result = self._run_validate("reject.chronos-carrier-bundle.owning-plane-agentplane.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("owningPlane must name a plane other than agentplane", result.stderr)

    def test_reject_missing_replay_ref(self) -> None:
        result = self._run_validate("reject.chronos-carrier-bundle.missing-replay-ref.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("spec.chronosCarrier.replayRef is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
