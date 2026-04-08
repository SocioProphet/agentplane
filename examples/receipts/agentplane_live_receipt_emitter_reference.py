#!/usr/bin/env python3
"""
Reference live-receipt assembler.
This is a thin integration example: merge normalized events into a MAIPJ run receipt.
It is intentionally strict about missing required fields and energy consistency.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


REQUIRED_EVENT_TYPES = {
    "workspace.locked",
    "context.pack.selected",
    "context.pack.fetched",
    "policy.evaluated",
    "placement.selected",
    "run.started",
    "run.completed",
    "evidence.sealed",
}


@dataclass
class ReceiptBuilder:
    trace_id: str
    receipt: Dict[str, Any] = field(default_factory=dict)
    seen: set = field(default_factory=set)

    def apply(self, event: Dict[str, Any]) -> None:
        if event.get("trace_id") != self.trace_id:
            raise ValueError("trace_id mismatch")
        et = event["event_type"]
        self.seen.add(et)
        p = event.get("payload", {})

        if "receipt_id" not in self.receipt:
            self.receipt["receipt_id"] = f"rpt_{self.trace_id}"
            self.receipt["trace_id"] = self.trace_id
            self.receipt["span_id"] = event.get("span_id")
            self.receipt["timestamp"] = event.get("ts")

        if et == "workspace.locked":
            self.receipt.setdefault("task", {}).update({
                "family": p["benchmark_family"],
                "case_id": p["case_id"],
                "mission_weight": p["mission_weight"],
                "utility_rubric_version": p["utility_rubric_version"],
                "latency_slo_ms": p["latency_slo_ms"],
                "risk_class": p["risk_class"],
            })
            self.receipt.setdefault("_workspace", {}).update({
                "workspace_manifest_id": p["workspace_manifest_id"],
                "workspace_lock_digest": p["workspace_lock_digest"],
            })

        elif et == "context.pack.selected":
            self.receipt.setdefault("context", {}).setdefault("pack_ids", [])
            self.receipt["context"]["pack_ids"] = p["pack_ids"]
            self.receipt["context"]["pack_digests"] = p["pack_digests"]
            self.receipt["context"]["policy_bundle_id"] = p["policy_bundle_id"]
            self.receipt["context"]["locality_class"] = p["locality_class"]

        elif et == "context.pack.fetched":
            self.receipt.setdefault("context", {}).update({
                "total_bytes": p["total_bytes"],
                "cache_hits": p["cache_hits"],
                "cache_misses": p["cache_misses"],
                "working_set_hit_rate": p["working_set_hit_rate"],
                "remote_fetch_count": p["remote_fetch_count"],
            })

        elif et == "placement.selected":
            self.receipt["placement"] = {
                "site": p["site"],
                "node_pool": p["node_pool"],
                "host_id": p["host_id"],
                "accelerator_type": p["accelerator_type"],
                "execution_mode": p["execution_mode"],
                "planner_version": p["planner_version"],
            }
            self.receipt["model_runtime"] = {
                "model_id": p["model_id"],
                "model_digest": p["model_digest"],
                "adapter_digest": p.get("adapter_digest"),
                "runtime_id": p["runtime_id"],
                "compiler_id": p.get("compiler_id"),
                "quantization": p.get("quantization"),
                "context_window_tokens": p.get("context_window_tokens"),
            }

        elif et == "run.completed":
            self.receipt.setdefault("energy_j", {}).update({
                "train_amortized": p.get("train_amortized", 0.0),
                "inference": p["inference_j"],
                "data_move": p["data_move_j"],
                "network": p["network_j"],
                "storage": p["storage_j"],
                "control": p["control_j"],
                "idle": p["idle_j"],
                "cooling_adjusted": p.get("cooling_adjusted_j", 0.0),
                "replay": p.get("replay_j", 0.0),
                "accounting_boundary": p["accounting_boundary"],
                "estimation_model": p["estimation_model"],
            })
            self.receipt.setdefault("outcome", {}).update({
                "quality": p["quality"],
                "calibration": p["calibration"],
                "robustness": p["robustness"],
                "latency_ms": p["latency_ms"],
                "replayable": p["replayable"],
            })

        elif et == "policy.evaluated":
            self.receipt.setdefault("outcome", {}).update({
                "policy_pass": p["policy_pass"],
                "human_approved": p.get("human_approved", False),
            })

        elif et == "evidence.sealed":
            self.receipt["evidence"] = {
                "input_digest": p["input_digest"],
                "output_digest": p["output_digest"],
                "evidence_refs": p["evidence_refs"],
                "attestation_refs": p.get("attestation_refs", []),
                "signature": p["signature"],
            }
            self.receipt["replay"] = {
                "supported": p["replay_supported"],
                "replay_manifest_id": p["replay_manifest_id"],
            }

    def finalize(self) -> Dict[str, Any]:
        missing = sorted(REQUIRED_EVENT_TYPES - self.seen)
        if missing:
            raise ValueError(f"missing required events: {missing}")

        e = self.receipt["energy_j"]
        total = (
            float(e.get("train_amortized", 0.0))
            + float(e["inference"])
            + float(e["data_move"])
            + float(e["network"])
            + float(e["storage"])
            + float(e["control"])
            + float(e["idle"])
            + float(e.get("cooling_adjusted", 0.0))
        )
        e["total"] = round(total, 6)
        return self.receipt


def build_receipt(trace_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    builder = ReceiptBuilder(trace_id)
    for ev in sorted(events, key=lambda x: x["ts"]):
        builder.apply(ev)
    return builder.finalize()


if __name__ == "__main__":
    import sys
    data = json.load(sys.stdin)
    trace_id = data["trace_id"]
    receipt = build_receipt(trace_id, data["events"])
    print(json.dumps(receipt, indent=2))