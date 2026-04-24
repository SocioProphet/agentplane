#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import emit_replay_artifact  # noqa: E402
import emit_run_artifact  # noqa: E402
import validate_bundle  # noqa: E402

EXPECTED = {
    "contentSpecRef": "urn:srcos:content-spec:sourceos-workstation",
    "overlayRefs": [
        "urn:srcos:overlay:customer-branding-acme",
        "urn:srcos:overlay:vpn-profile-default",
    ],
    "buildRequestRef": "urn:srcos:build-request:sourceos-workstation-dev-0001",
    "releaseManifestRef": "urn:srcos:release:sourceos-workstation-dev-0001",
    "enrollmentProfileRef": "urn:srcos:enrollment-profile:default-workstation",
    "evidenceBundleRef": "urn:srcos:evidence-bundle:sourceos-workstation-dev-0001",
    "localExecutionProtocolRef": "urn:srcos:contract:workstation-contracts:m2-ipc:v1.0",
    "remoteExecutionProtocolRef": "urn:srcos:protocol:tritrpc:v1",
}


class SourceOSBindingProjectionTests(unittest.TestCase):
    def test_preferred_integration_refs_path_projects_consistently(self) -> None:
        spec = {"integrationRefs": {"sourceos": dict(EXPECTED)}}

        self.assertEqual(validate_bundle.extract_sourceos_bindings(spec), EXPECTED)
        self.assertEqual(emit_run_artifact.extract_sourceos_bindings(spec), EXPECTED)
        self.assertEqual(emit_replay_artifact.extract_sourceos_bindings(spec), EXPECTED)

    def test_legacy_sourceos_build_release_path_projects_consistently(self) -> None:
        spec = {"sourceosBuildRelease": dict(EXPECTED)}

        self.assertEqual(validate_bundle.extract_sourceos_bindings(spec), EXPECTED)
        self.assertEqual(emit_run_artifact.extract_sourceos_bindings(spec), EXPECTED)
        self.assertEqual(emit_replay_artifact.extract_sourceos_bindings(spec), EXPECTED)

    def test_empty_bindings_project_to_empty_object(self) -> None:
        spec = {}

        self.assertEqual(validate_bundle.extract_sourceos_bindings(spec), {})
        self.assertEqual(emit_run_artifact.extract_sourceos_bindings(spec), {})
        self.assertEqual(emit_replay_artifact.extract_sourceos_bindings(spec), {})

    def test_validator_rejects_non_array_overlay_refs(self) -> None:
        spec = {"integrationRefs": {"sourceos": {"overlayRefs": "not-an-array"}}}

        with self.assertRaises(SystemExit):
            validate_bundle.extract_sourceos_bindings(spec)


if __name__ == "__main__":
    unittest.main()
