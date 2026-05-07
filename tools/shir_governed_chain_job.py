#!/usr/bin/env python3
"""Run or project the governed SHIR chain as an AgentPlane job.

This fixture-grade utility can invoke the fabric-suite SHIR governed chain and
then project its chain receipt into an AgentPlane run record. It can also
project an existing chain receipt. No PyTorch, PyG, DGL, or LLM runtime is
required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"
JOB_TYPE = "shir.governed_chain.v0.1"
CONFIG_HASH = "sha256:agentplane-shir-governed-chain-job-v0.1-default"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, doc: Dict[str, Any]) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cmd(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def chain_runner_path(fabric_suite: Path) -> Path:
    return fabric_suite / "packs" / "shir-governed-chain" / "tools" / "run_shir_chain.py"


def default_input_path(fabric_suite: Path) -> Path:
    return fabric_suite / "packs" / "rdf-to-shir" / "fixtures" / "topolvm.ttl"


def invoke_chain(fabric_suite: Path, input_ref: Path, out_ref: Path, schema_ref: Optional[Path], timestamp: str) -> Path:
    runner = chain_runner_path(fabric_suite)
    if not runner.exists():
        raise FileNotFoundError(f"SHIR governed chain runner not found: {runner}")
    cmd = [sys.executable, str(runner), "--input", str(input_ref), "--out-dir", str(out_ref), "--timestamp", timestamp]
    if schema_ref:
        cmd.extend(["--schema-dir", str(schema_ref)])
    run_cmd(cmd)
    receipt_path = out_ref / "chain_run_receipt.json"
    if not receipt_path.exists():
        raise FileNotFoundError(f"chain runner did not emit {receipt_path}")
    return receipt_path


def infer_failure_class(chain_receipt: Dict[str, Any], chain_error_path: Optional[Path]) -> Optional[str]:
    if chain_error_path and chain_error_path.exists():
        error = load_json(chain_error_path)
        message = str(error.get("error_message", "")).lower()
        if "parse" in message or "turtle" in message or "rdf" in message:
            return "parse_failure"
        if "schema" in message or "validat" in message:
            return "schema_validation_failure"
        return "chain_runtime_failure"
    decision = chain_receipt.get("policy_decision", {}).get("decision")
    params = chain_receipt.get("transform", {}).get("parameters", {})
    stage_summary = params.get("stage_summary", {})
    if decision in {"DENY", "QUARANTINE"}:
        return "policy_denied"
    if stage_summary.get("semantic_leakage_risk") == "BLOCKING":
        return "semantic_leakage_blocking"
    if stage_summary.get("projection_loss_risk") == "ESCALATED":
        return "projection_loss_blocking"
    return None


def state_from_policy(policy_mode: str, chain_receipt: Dict[str, Any], failure_class: Optional[str]) -> str:
    if failure_class:
        return "failed_closed" if policy_mode == "fail_closed" else "requires_review"
    decision = chain_receipt.get("policy_decision", {}).get("decision")
    if decision == "ALLOW":
        return "succeeded"
    if decision == "REVIEW_REQUIRED":
        return "requires_review"
    if decision in {"DENY", "QUARANTINE"}:
        return "failed_closed" if policy_mode == "fail_closed" else "requires_review"
    return "requires_review"


def collect_artifact_refs(out_ref: Path) -> List[Dict[str, str]]:
    artifacts: List[Dict[str, str]] = []
    if not out_ref.exists():
        return artifacts
    for path in sorted(out_ref.rglob("*.json")):
        artifacts.append({"artifact_ref": str(path), "relative_path": str(path.relative_to(out_ref)), "sha256": sha256_file(path)})
    return artifacts


def build_run_record(
    trace_id: str,
    input_ref: Path,
    out_ref: Path,
    fabric_suite: Path,
    schema_ref: Optional[Path],
    ontology_profile_ref: str,
    policy_mode: str,
    relation_strategy: str,
    chain_receipt_path: Optional[Path],
    timestamp: str,
) -> Dict[str, Any]:
    chain_receipt: Dict[str, Any] = {}
    if chain_receipt_path and chain_receipt_path.exists():
        chain_receipt = load_json(chain_receipt_path)
    failure_class = infer_failure_class(chain_receipt, out_ref / "chain_error.json")
    state = state_from_policy(policy_mode, chain_receipt, failure_class) if chain_receipt else "failed_closed"
    params = chain_receipt.get("transform", {}).get("parameters", {}) if chain_receipt else {}
    return {
        "job_type": JOB_TYPE,
        "trace_id": trace_id,
        "state": state,
        "policy_mode": policy_mode,
        "policy_decision": chain_receipt.get("policy_decision", {}).get("decision", "QUARANTINE"),
        "input_ref": str(input_ref),
        "schema_ref": str(schema_ref) if schema_ref else None,
        "ontology_profile_ref": ontology_profile_ref,
        "fabric_suite_ref": str(fabric_suite),
        "out_ref": str(out_ref),
        "relation_strategy": relation_strategy,
        "chain_receipt_ref": str(chain_receipt_path) if chain_receipt_path else None,
        "chain_receipt_sha256": sha256_file(chain_receipt_path) if chain_receipt_path and chain_receipt_path.exists() else None,
        "stage_receipts": params.get("stage_receipts", {}),
        "stage_summary": params.get("stage_summary", {}),
        "artifact_refs": collect_artifact_refs(out_ref),
        "failure_class": failure_class,
        "receipt_id": chain_receipt.get("receipt_id"),
        "replay": chain_receipt.get("replay", {"replayable": False, "config_hash": CONFIG_HASH}),
        "created_at": timestamp,
    }


def validate_record(record: Dict[str, Any]) -> None:
    required = ["job_type", "trace_id", "state", "policy_mode", "policy_decision", "input_ref", "out_ref", "chain_receipt_ref", "artifact_refs"]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"run record missing required keys: {missing}")
    if record["job_type"] != JOB_TYPE:
        raise ValueError(f"unexpected job_type: {record['job_type']}")
    if record["state"] not in {"succeeded", "requires_review", "failed_closed"}:
        raise ValueError(f"unexpected state: {record['state']}")
    if record["policy_mode"] not in {"advisory", "review_required", "fail_closed"}:
        raise ValueError(f"unexpected policy_mode: {record['policy_mode']}")


def build_error_record(trace_id: str, input_ref: Path, out_ref: Path, error: Exception, timestamp: str) -> Dict[str, Any]:
    return {
        "job_type": JOB_TYPE,
        "trace_id": trace_id,
        "state": "failed_closed",
        "policy_mode": "fail_closed",
        "policy_decision": "QUARANTINE",
        "input_ref": str(input_ref),
        "out_ref": str(out_ref),
        "chain_receipt_ref": None,
        "artifact_refs": collect_artifact_refs(out_ref),
        "failure_class": "chain_runtime_failure",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "created_at": timestamp,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the governed SHIR chain as an AgentPlane job fixture.")
    parser.add_argument("--fabric-suite", required=True, help="Path to prophet-platform-fabric-mlops-ts-suite checkout")
    parser.add_argument("--input-ref", help="Input Turtle file. Defaults to fabric suite TopoLVM fixture.")
    parser.add_argument("--schema-ref", help="Path to semantic-serdes schemas directory")
    parser.add_argument("--ontology-profile-ref", default="ontogenesis.shir.v0.1")
    parser.add_argument("--out-ref", required=True, help="Output directory for retained artifacts")
    parser.add_argument("--trace-id", default="trace.shir.governed_chain.fixture.001")
    parser.add_argument("--policy-mode", default="fail_closed", choices=["advisory", "review_required", "fail_closed"])
    parser.add_argument("--relation-strategy", default="relation_node")
    parser.add_argument("--timestamp", default=DEFAULT_TIMESTAMP)
    parser.add_argument("--from-chain-receipt", help="Skip execution and project an existing chain receipt")
    args = parser.parse_args()

    fabric_suite = Path(args.fabric_suite)
    input_ref = Path(args.input_ref) if args.input_ref else default_input_path(fabric_suite)
    schema_ref = Path(args.schema_ref) if args.schema_ref else None
    out_ref = Path(args.out_ref)
    out_ref.mkdir(parents=True, exist_ok=True)

    try:
        chain_receipt_path = Path(args.from_chain_receipt) if args.from_chain_receipt else invoke_chain(fabric_suite, input_ref, out_ref, schema_ref, args.timestamp)
        record = build_run_record(args.trace_id, input_ref, out_ref, fabric_suite, schema_ref, args.ontology_profile_ref, args.policy_mode, args.relation_strategy, chain_receipt_path, args.timestamp)
        validate_record(record)
        record_path = out_ref / "agentplane_run_record.json"
        write_json(record_path, record)
        print(json.dumps({"run_record": str(record_path), "state": record["state"], "policy_decision": record["policy_decision"]}, indent=2, sort_keys=True))
        return 0 if record["state"] != "failed_closed" else 2
    except Exception as exc:  # noqa: BLE001 - fixture tool must preserve a failure record.
        error_record = build_error_record(args.trace_id, input_ref, out_ref, exc, args.timestamp)
        write_json(out_ref / "agentplane_run_record.json", error_record)
        print(f"SHIR AgentPlane job failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
