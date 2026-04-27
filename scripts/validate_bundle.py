#!/usr/bin/env python3
import json, sys, os, datetime
from pathlib import Path

from evaluate_control_matrix_gate import ControlGateError, evaluate_bundle_gate, write_gate_artifact

SOURCEOS_BINDING_KEYS = {
    "contentSpecRef",
    "overlayRefs",
    "buildRequestRef",
    "releaseManifestRef",
    "enrollmentProfileRef",
    "evidenceBundleRef",
    "localExecutionProtocolRef",
    "remoteExecutionProtocolRef",
}


def die(msg: str, code: int = 2) -> None:
    print(f"[validate] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _require_mapping(obj, path: str):
    if not isinstance(obj, dict):
        die(f"{path} must be an object", 2)
    return obj


def _require_non_empty(obj: dict, path: str, keys: tuple[str, ...]) -> None:
    for key in keys:
        value = obj.get(key)
        if value is None or value == "" or value == []:
            die(f"{path}.{key} is required for SourceOS image-production bundles", 2)


def extract_sourceos_bindings(spec: dict) -> dict:
    integration_refs = spec.get("integrationRefs") or {}
    sourceos = integration_refs.get("sourceos") or spec.get("sourceosBuildRelease") or {}
    if not sourceos:
        return {}
    if not isinstance(sourceos, dict):
        die("spec.integrationRefs.sourceos must be an object when present", 2)

    out = {}
    for key in SOURCEOS_BINDING_KEYS:
        value = sourceos.get(key)
        if value not in (None, "", []):
            out[key] = value

    if "overlayRefs" in out and not isinstance(out["overlayRefs"], list):
        die("spec.integrationRefs.sourceos.overlayRefs must be an array when present", 2)
    return out


def validate_sourceos_image_production(spec: dict) -> dict:
    """Validate the optional SourceOS image-production lane.

    The lane is intentionally optional so existing bundles continue to pass. When a
    bundle declares any SourceOS image-production or socios automation intent, we
    fail closed unless the authority refs needed for governed execution are present.
    """
    sourceos_present = "sourceos" in spec
    automation_present = "sociosAutomation" in spec
    outputs_present = "outputs" in spec

    if not (sourceos_present or automation_present or outputs_present):
        return {"enabled": False, "result": "not_applicable"}

    sourceos = _require_mapping(spec.get("sourceos") or {}, "spec.sourceos")
    automation = _require_mapping(spec.get("sociosAutomation") or {}, "spec.sociosAutomation")
    outputs = _require_mapping(spec.get("outputs") or {}, "spec.outputs")

    _require_non_empty(
        sourceos,
        "spec.sourceos",
        (
            "artifactTruthRef",
            "flavorRef",
            "installerProfileRef",
            "channelRef",
            "manifestRef",
            "sourceosSpecRef",
        ),
    )
    _require_non_empty(
        automation,
        "spec.sociosAutomation",
        (
            "substrateDocRef",
            "katelloContentModelRef",
            "tektonPipelineRef",
            "katelloProduct",
            "katelloRepository",
            "katelloLifecycleEnvironment",
        ),
    )

    lifecycle = automation.get("katelloLifecycleEnvironment")
    if lifecycle not in {"dev", "qa", "prod", "site", "custom"}:
        die("spec.sociosAutomation.katelloLifecycleEnvironment must be one of dev, qa, prod, site, custom", 2)

    secret_refs = spec.get("secrets", {}).get("required") or []
    if any(not isinstance(ref, str) or not ref.strip() for ref in secret_refs):
        die("spec.secrets.required entries must be non-empty secret references", 2)

    inline_secret_keys = {
        key
        for key in automation
        if key.lower() in {"password", "token", "secret", "username", "katellopassword", "katellotoken"}
    }
    if inline_secret_keys:
        die(
            "spec.sociosAutomation must not contain inline secret material; use spec.secrets refs instead "
            f"(found: {sorted(inline_secret_keys)})",
            2,
        )

    expected_output_refs = [
        "bootReleaseSetRef",
        "evidenceBundleRef",
        "katelloContentRef",
        "ostreeRef",
        "releaseSetRef",
        "smokeReceiptRef",
    ]
    declared_outputs = [key for key in expected_output_refs if outputs.get(key)]

    return {
        "enabled": True,
        "result": "pass",
        "artifactTruthRef": sourceos.get("artifactTruthRef"),
        "flavorRef": sourceos.get("flavorRef"),
        "installerProfileRef": sourceos.get("installerProfileRef"),
        "channelRef": sourceos.get("channelRef"),
        "manifestRef": sourceos.get("manifestRef"),
        "sourceosSpecRef": sourceos.get("sourceosSpecRef"),
        "tektonPipelineRef": automation.get("tektonPipelineRef"),
        "katelloProduct": automation.get("katelloProduct"),
        "katelloRepository": automation.get("katelloRepository"),
        "katelloLifecycleEnvironment": lifecycle,
        "declaredOutputs": declared_outputs,
    }


def main() -> int:
    if len(sys.argv) != 2:
        die("usage: scripts/validate_bundle.py <path/to/bundle.json>", 2)

    bundle_path = sys.argv[1]
    if not os.path.exists(bundle_path):
        die(f"bundle not found: {bundle_path}", 2)

    with open(bundle_path, "r", encoding="utf-8") as f:
        try:
            b = json.load(f)
        except json.JSONDecodeError as e:
            die(f"invalid JSON: {e}", 2)

    # Minimal contract checks (v0.1)
    if b.get("apiVersion") != "agentplane.socioprophet.org/v0.1":
        die("apiVersion must be agentplane.socioprophet.org/v0.1", 2)
    if b.get("kind") != "Bundle":
        die("kind must be Bundle", 2)

    md = b.get("metadata") or {}
    spec = b.get("spec") or {}

    for k in ("name", "version", "createdAt"):
        if k not in md:
            die(f"metadata.{k} is required", 2)

    lp = md.get("licensePolicy") or {}
    if lp.get("allowAGPL", False) is not False:
        die("metadata.licensePolicy.allowAGPL must be false", 2)

    for k in ("vm", "policy", "secrets", "artifacts", "smoke"):
        if k not in spec:
            die(f"spec.{k} is required", 2)

    sourceos_bindings = extract_sourceos_bindings(spec)
    sourceos_image_production_gate = validate_sourceos_image_production(spec)

    pol = spec.get("policy") or {}
    mrs = pol.get("maxRunSeconds")
    if mrs is None:
        die("spec.policy.maxRunSeconds is required", 2)
    if not isinstance(mrs, int) or mrs < 5 or mrs > 3600:
        die("spec.policy.maxRunSeconds must be an int in [5, 3600]", 2)

    abstract_reasoning = pol.get("abstractReasoning") or {}
    if abstract_reasoning:
        reasoning_class = abstract_reasoning.get("reasoningClass", "REACTIVE")
        verification_mode = abstract_reasoning.get("verificationMode", "NONE")
        llm_only_forbidden = bool(abstract_reasoning.get("llmOnlyForbidden", False))
        requires_counterexample_search = bool(abstract_reasoning.get("requiresCounterexampleSearch", False))
        requires_program_candidate = bool(abstract_reasoning.get("requiresProgramCandidate", False))
        requires_backtracking_capability = bool(abstract_reasoning.get("requiresBacktrackingCapability", False))

        allowed_reasoning_classes = {"REACTIVE", "RETRIEVAL", "ABSTRACT", "CAUSAL", "PROGRAM_INDUCTION"}
        allowed_verification_modes = {
            "NONE",
            "POLICY_ONLY",
            "COUNTEREXAMPLE_SEARCH",
            "PROGRAM_EXECUTION",
            "CAUSAL_CHECK",
            "HUMAN_REVIEW",
            "COMPOSITE",
        }
        if reasoning_class not in allowed_reasoning_classes:
            die(f"spec.policy.abstractReasoning.reasoningClass must be one of {sorted(allowed_reasoning_classes)}", 2)
        if verification_mode not in allowed_verification_modes:
            die(f"spec.policy.abstractReasoning.verificationMode must be one of {sorted(allowed_verification_modes)}", 2)
        if reasoning_class in {"ABSTRACT", "PROGRAM_INDUCTION"} and llm_only_forbidden and verification_mode == "NONE":
            die("abstractReasoning forbids llm-only evaluation when reasoningClass is ABSTRACT or PROGRAM_INDUCTION", 2)
        if requires_program_candidate and not abstract_reasoning.get("programCandidateRef"):
            die("abstractReasoning requires programCandidateRef", 2)
        if requires_counterexample_search and not (abstract_reasoning.get("counterexampleRefs") or []):
            die("abstractReasoning requires counterexampleRefs", 2)
        if requires_backtracking_capability and not abstract_reasoning.get("backtrackingCapable", False):
            die("abstractReasoning requires backtrackingCapable=true", 2)

    vm = spec["vm"]
    backend_intent = vm.get("backendIntent")
    allowed = {"qemu", "microvm", "lima-process", "fleet"}
    if backend_intent not in allowed:
        die(f"spec.vm.backendIntent must be one of {sorted(allowed)}", 2)
    if "modulePath" not in vm or "backendIntent" not in vm:
        die("spec.vm.modulePath and spec.vm.backendIntent are required", 2)

    artifacts = spec["artifacts"]
    out_dir = artifacts.get("outDir")
    if not out_dir:
        die("spec.artifacts.outDir is required", 2)

    os.makedirs(out_dir, exist_ok=True)
    gate_artifact_path = Path(out_dir) / "control-gate-artifact.json"
    try:
        gate_artifact = evaluate_bundle_gate(b, Path(bundle_path))
        write_gate_artifact(gate_artifact, gate_artifact_path)
    except ControlGateError as e:
        die(str(e), 2)

    if gate_artifact["result"] != "allow":
        die(
            f"control matrix gate denied bundle: {gate_artifact['reason']} (rows={gate_artifact['blockingRowIds'] or gate_artifact['candidateRowIds']})",
            2,
        )

    report = {
        "kind": "ValidationArtifact",
        "bundle": f'{md.get("name")}@{md.get("version")}',
        "bundlePath": os.path.abspath(bundle_path),
        "validatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "result": "pass",
        "sourceosBindings": sourceos_bindings,
        "sourceosImageProductionGate": sourceos_image_production_gate,
        "controlGate": {
            "result": gate_artifact["result"],
            "reason": gate_artifact["reason"],
            "artifactPath": str(gate_artifact_path),
            "matchedRowIds": gate_artifact["matchedRowIds"],
        },
        "abstractGate": {
            "reasoningClass": gate_artifact["gateContext"].get("reasoning_class"),
            "verificationMode": gate_artifact["gateContext"].get("verification_mode"),
            "llmOnlyForbidden": gate_artifact["gateContext"].get("llm_only_forbidden"),
            "requiresCounterexampleSearch": gate_artifact["gateContext"].get("requires_counterexample_search"),
            "requiresProgramCandidate": gate_artifact["gateContext"].get("requires_program_candidate"),
            "requiresBacktrackingCapability": gate_artifact["gateContext"].get("requires_backtracking_capability"),
        },
    }
    report_path = os.path.join(out_dir, "validation-artifact.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print(f"[validate] OK: wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
