#!/usr/bin/env python3
"""Validate BankingBundleStagingReview v0.1 records.

This validator is intentionally static. It checks the review manifest and file
posture records without executing smoke scripts, booting VM definitions, opening
network access, or admitting bundles into runtime.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "banking-bundle-staging-review.v0.1.schema.json"

REQUIRED_TOP_LEVEL = {
    "schemaVersion",
    "recordType",
    "review_id",
    "source_branch",
    "issue_refs",
    "nonProductionOnly",
    "review_scope",
    "overall_decision",
    "bundle_count",
    "bundles",
    "non_goals",
    "recorded_at",
    "receipt_hash",
}
REQUIRED_NON_GOALS = {
    "bundle_execution",
    "smoke_script_execution",
    "vm_boot",
    "network_access",
    "provider_integration",
    "production_banking_claims",
    "policy_pack_promotion",
    "runtime_admission",
    "workspace_mutation",
}
REQUIRED_BUNDLE_FIELDS = {
    "bundle_name",
    "domain",
    "purpose",
    "source_files",
    "classification",
    "target_repo_question",
    "network_posture",
    "artifact_write_posture",
    "policy_pack_status",
    "smoke_script_posture",
    "vm_definition_posture",
    "claim_posture",
    "bundle_admission",
    "review_findings",
}
ALLOWED_DECISIONS = {"metadata_only_capture", "hold_for_domain_review", "reject"}
ALLOWED_BUNDLE_ADMISSIONS = {"metadata_only", "hold", "reject"}
ALLOWED_CLASSIFICATIONS = {"staging_fixture", "design_example", "canonical_fixture", "out_of_scope"}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)}: expected JSON object")
    return payload


def require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def require_bool(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        fail(f"{key}: expected boolean")
    return value


def require_string_list(record: dict[str, Any], key: str, *, min_items: int = 1) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list) or len(value) < min_items:
        fail(f"{key}: expected array with at least {min_items} item(s)")
    seen: set[str] = set()
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            fail(f"{key}: expected non-empty string entries")
        if item in seen:
            fail(f"{key}: duplicate entry {item}")
        seen.add(item)
        out.append(item)
    return out


def validate_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("type") != "object":
        fail("schema must describe an object")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED_TOP_LEVEL - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agentplane.banking-bundle-staging-review.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "BankingBundleStagingReview":
        fail("recordType const mismatch")


def validate_network_posture(bundle_name: str, posture: Any) -> None:
    if not isinstance(posture, dict):
        fail(f"{bundle_name}.network_posture: expected object")
    mode = require_string(posture, "declared_network_mode")
    dns = require_bool(posture, "dns_egress")
    https = require_bool(posture, "https_egress")
    first_capture_allowed = require_bool(posture, "first_capture_allowed")
    if mode not in {"network_off", "nat_dns_https", "unknown"}:
        fail(f"{bundle_name}.network_posture.declared_network_mode invalid: {mode}")
    if mode == "network_off" and (dns or https):
        fail(f"{bundle_name}: network_off cannot declare DNS/HTTPS egress")
    if (dns or https or mode == "nat_dns_https") and first_capture_allowed:
        fail(f"{bundle_name}: network egress must not be allowed in first metadata-only capture")


def validate_artifact_write_posture(bundle_name: str, posture: Any) -> None:
    if not isinstance(posture, dict):
        fail(f"{bundle_name}.artifact_write_posture: expected object")
    writes = require_bool(posture, "writes_artifacts")
    paths = require_string_list(posture, "writable_paths", min_items=0)
    first_capture_allowed = require_bool(posture, "first_capture_allowed")
    if writes and not paths:
        fail(f"{bundle_name}: artifact writes require explicit writable_paths")
    if writes and first_capture_allowed:
        fail(f"{bundle_name}: writable artifact paths must not be enabled in first metadata-only capture")


def validate_policy_pack_status(bundle_name: str, status: Any) -> None:
    if not isinstance(status, dict):
        fail(f"{bundle_name}.policy_pack_status: expected object")
    policy_ref = require_string(status, "policy_pack_ref")
    hash_status = require_string(status, "hash_status")
    requires_pin = require_bool(status, "first_capture_requires_pin")
    if hash_status not in {"pinned", "unset_placeholder", "unknown"}:
        fail(f"{bundle_name}.policy_pack_status.hash_status invalid: {hash_status}")
    if (policy_ref == "UNSET" or hash_status == "unset_placeholder") and not requires_pin:
        fail(f"{bundle_name}: unset policy-pack placeholders must require pinning before promotion")


def validate_script_and_vm_posture(bundle_name: str, bundle: dict[str, Any]) -> None:
    script = bundle.get("smoke_script_posture")
    if not isinstance(script, dict):
        fail(f"{bundle_name}.smoke_script_posture: expected object")
    if require_bool(script, "present") and require_bool(script, "executable_in_first_capture"):
        fail(f"{bundle_name}: smoke scripts must not execute in metadata-only capture")

    vm = bundle.get("vm_definition_posture")
    if not isinstance(vm, dict):
        fail(f"{bundle_name}.vm_definition_posture: expected object")
    if require_bool(vm, "present") and require_bool(vm, "bootable_in_first_capture"):
        fail(f"{bundle_name}: VM definitions must not boot in metadata-only capture")


def validate_source_files(bundle_name: str, source_files: list[str]) -> None:
    expected_prefix = f"bundles/{bundle_name}/"
    if not any(path == f"{expected_prefix}bundle.json" for path in source_files):
        fail(f"{bundle_name}: source_files must include bundle.json")
    if not any(path == f"{expected_prefix}smoke.sh" for path in source_files):
        fail(f"{bundle_name}: source_files must record smoke.sh presence")
    if not any(path == f"{expected_prefix}vm.nix" for path in source_files):
        fail(f"{bundle_name}: source_files must record vm.nix presence")
    if any(path.startswith("/") or ".." in Path(path).parts for path in source_files):
        fail(f"{bundle_name}: source_files must stay repo-relative")


def validate_bundle(bundle: Any) -> None:
    if not isinstance(bundle, dict):
        fail("bundles entries must be objects")
    missing = sorted(REQUIRED_BUNDLE_FIELDS - set(bundle))
    if missing:
        fail(f"bundle missing required fields: {missing}")
    bundle_name = require_string(bundle, "bundle_name")
    if require_string(bundle, "domain") != "banking-twin":
        fail(f"{bundle_name}: domain must be banking-twin")
    if require_string(bundle, "classification") not in ALLOWED_CLASSIFICATIONS:
        fail(f"{bundle_name}: invalid classification")
    if require_string(bundle, "bundle_admission") not in ALLOWED_BUNDLE_ADMISSIONS:
        fail(f"{bundle_name}: invalid bundle_admission")
    if require_string(bundle, "claim_posture") not in {"domain_language_only", "no_production_claims", "requires_claim_review"}:
        fail(f"{bundle_name}: invalid claim_posture")
    source_files = require_string_list(bundle, "source_files")
    validate_source_files(bundle_name, source_files)
    validate_network_posture(bundle_name, bundle.get("network_posture"))
    validate_artifact_write_posture(bundle_name, bundle.get("artifact_write_posture"))
    validate_policy_pack_status(bundle_name, bundle.get("policy_pack_status"))
    validate_script_and_vm_posture(bundle_name, bundle)
    require_string_list(bundle, "review_findings", min_items=0)


def validate_review(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_TOP_LEVEL - set(record))
    if missing:
        fail(f"missing required fields: {missing}")
    if record["schemaVersion"] != "agentplane.banking-bundle-staging-review.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "BankingBundleStagingReview":
        fail("recordType mismatch")
    require_string(record, "review_id")
    if require_string(record, "source_branch") != "banking-twin/agentplane-execution-bundles-v0-1":
        fail("source_branch must identify the audited banking-twin bundle branch")
    require_string_list(record, "issue_refs")
    if record.get("nonProductionOnly") is not True:
        fail("nonProductionOnly must be true")
    if record.get("review_scope") != "metadata_only_no_execution":
        fail("review_scope must be metadata_only_no_execution")
    if require_string(record, "overall_decision") not in ALLOWED_DECISIONS:
        fail("invalid overall_decision")
    bundles = record.get("bundles")
    if not isinstance(bundles, list) or not bundles:
        fail("bundles must be a non-empty array")
    if record.get("bundle_count") != len(bundles):
        fail("bundle_count must match bundles length")
    seen: set[str] = set()
    for bundle in bundles:
        validate_bundle(bundle)
        name = bundle["bundle_name"]
        if name in seen:
            fail(f"duplicate bundle_name: {name}")
        seen.add(name)
    missing_non_goals = sorted(REQUIRED_NON_GOALS - set(require_string_list(record, "non_goals")))
    if missing_non_goals:
        fail(f"non_goals missing required entries: {missing_non_goals}")
    require_string(record, "recorded_at")
    if not require_string(record, "receipt_hash").startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_banking_bundle_staging_review.py <review.json>", file=sys.stderr)
        return 2
    try:
        validate_schema_contract(load_json(SCHEMA))
        validate_review(load_json(Path(argv[1])))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {argv[1]} validates as BankingBundleStagingReview v0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
