"""Validate a SourceOS image-production bundle against blocking conditions.

Usage:
    python3 validate_sourceos_bundle.py --bundle <path/to/bundle.json>

Exit codes:
    0  — ok (no block-severity findings)
    2  — one or more blocking findings

Output: JSON to stdout:
    {"ok": bool, "findings": [{"condition": str, "severity": "block"|"warn", "message": str}]}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _get(d: dict, *keys: str) -> Any:
    """Safely traverse nested dicts; returns None if any key is missing."""
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)  # type: ignore[assignment]
    return d


def validate_bundle(bundle: dict[str, Any], bundle_dir: Path) -> dict[str, Any]:
    """Run all blocking-condition checks and return a findings dict."""
    findings: list[dict[str, str]] = []

    def block(condition: str, message: str) -> None:
        findings.append({"condition": condition, "severity": "block", "message": message})

    def warn(condition: str, message: str) -> None:
        findings.append({"condition": condition, "severity": "warn", "message": message})

    # 1. AGPL must be false
    allow_agpl = _get(bundle, "metadata", "licensePolicy", "allowAGPL")
    if allow_agpl is not False:
        block("license_policy.allowAGPL", f"metadata.licensePolicy.allowAGPL must be false; got {allow_agpl!r}")

    # 2. git rev must not be UNSET
    rev = _get(bundle, "metadata", "source", "git", "rev")
    if not rev:
        block("metadata.source.git.rev", "metadata.source.git.rev is missing")
    elif rev == "UNSET":
        warn("metadata.source.git.rev", "metadata.source.git.rev is UNSET — must be set before production use")

    # 3. artifactTruthRef required
    truth_ref = _get(bundle, "spec", "sourceos", "artifactTruthRef")
    if not truth_ref:
        block("spec.sourceos.artifactTruthRef", "spec.sourceos.artifactTruthRef is required and must be non-empty")

    # 4. humanGateRequired must be present
    human_gate = _get(bundle, "spec", "policy", "humanGateRequired")
    if human_gate is None:
        block("spec.policy.humanGateRequired", "spec.policy.humanGateRequired is required")

    # 5. policy lane must be staging or prod
    lane = _get(bundle, "spec", "policy", "lane")
    if lane not in ("staging", "prod"):
        block("spec.policy.lane", f"spec.policy.lane must be 'staging' or 'prod'; got {lane!r}")

    # 6. policyPackRef must be non-empty (warn if UNSET, block if missing)
    pack_ref = _get(bundle, "spec", "policy", "policyPackRef")
    if not pack_ref:
        block("spec.policy.policyPackRef", "spec.policy.policyPackRef is required")
    elif pack_ref == "UNSET":
        warn("spec.policy.policyPackRef", "spec.policy.policyPackRef is UNSET — must be set before production use")

    # 7. secrets.required must be a non-empty list
    secrets_required = _get(bundle, "spec", "secrets", "required")
    if not isinstance(secrets_required, list) or len(secrets_required) == 0:
        block("spec.secrets.required", "spec.secrets.required must be a non-empty list of secret references")

    # 8. No inline secrets (no 'value' or 'inlineValue' keys anywhere in spec.secrets)
    def _has_inline(obj: Any) -> bool:
        if isinstance(obj, dict):
            if "value" in obj or "inlineValue" in obj:
                return True
            return any(_has_inline(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_has_inline(item) for item in obj)
        return False

    secrets_block = _get(bundle, "spec", "secrets") or {}
    if _has_inline(secrets_block):
        block("spec.secrets.inline", "spec.secrets must not contain inline secret values (no 'value' or 'inlineValue' keys)")

    # 9. sociosAutomation: if present, required sub-fields must be non-empty
    socios = _get(bundle, "spec", "sociosAutomation")
    if socios is not None:
        for field_name in ("tektonPipelineRef", "katelloProduct", "katelloRepository", "katelloLifecycleEnvironment"):
            val = socios.get(field_name) if isinstance(socios, dict) else None
            if not val:
                block(
                    f"spec.sociosAutomation.{field_name}",
                    f"spec.sociosAutomation.{field_name} is required when spec.sociosAutomation is present",
                )

    # 10. At least one output ref must be present and not UNSET
    outputs = _get(bundle, "spec", "outputs") or {}
    output_keys = ("releaseSetRef", "bootReleaseSetRef", "katelloContentRef", "evidenceBundleRef")
    present_outputs = [k for k in output_keys if outputs.get(k) and outputs[k] != "UNSET"]
    if not present_outputs:
        block("spec.outputs", "at least one output ref must be present and not 'UNSET' in spec.outputs")

    # 11. smoke script must exist if declared.
    # Paths are tried in order: relative to bundle_dir, then relative to CWD
    # (repo root). Bundle specs typically use repo-root-relative paths.
    smoke_script = _get(bundle, "spec", "smoke", "script")
    if smoke_script:
        candidates = [(bundle_dir / smoke_script).resolve(), (Path.cwd() / smoke_script).resolve()]
        if not any(p.exists() for p in candidates):
            block("spec.smoke.script", f"spec.smoke.script '{smoke_script}' not found (checked bundle dir and repo root)")

    ok = not any(f["severity"] == "block" for f in findings)
    return {"ok": ok, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, help="Path to bundle.json")
    args = parser.parse_args(argv)

    bundle_path = Path(args.bundle).resolve()
    if not bundle_path.exists():
        result = {"ok": False, "findings": [{"condition": "bundle_file", "severity": "block", "message": f"bundle file not found: {bundle_path}"}]}
        print(json.dumps(result, indent=2))
        return 2

    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        result = {"ok": False, "findings": [{"condition": "bundle_parse", "severity": "block", "message": f"failed to parse bundle: {exc}"}]}
        print(json.dumps(result, indent=2))
        return 2

    result = validate_bundle(bundle, bundle_path.parent)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
