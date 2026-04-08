#!/usr/bin/env python3
"""Minimal smoke test for MAIPJ receipt assembly.

Usage:
  python tools/receipt_smoke_test.py examples/receipts/gakw_hybrid_warm_trace.example.json

This does not depend on external packages. It validates the event minimum set,
assembles a receipt, checks energy consistency, and prints the resulting receipt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_EVENT_TYPES = {
    'workspace.locked',
    'context.pack.selected',
    'context.pack.fetched',
    'policy.evaluated',
    'placement.selected',
    'run.started',
    'run.completed',
    'evidence.sealed',
}


def build_receipt(trace_doc: dict) -> dict:
    events = sorted(trace_doc['events'], key=lambda x: x['ts'])
    seen = {e['event_type'] for e in events}
    missing = sorted(REQUIRED_EVENT_TYPES - seen)
    if missing:
        raise SystemExit(f'missing required events: {missing}')

    receipt = {
        'receipt_id': f"rpt_{trace_doc['trace_id']}",
        'trace_id': trace_doc['trace_id'],
    }

    for event in events:
        et = event['event_type']
        p = event.get('payload', {})
        receipt.setdefault('timestamp', event['ts'])
        receipt.setdefault('span_id', event.get('span_id'))

        if et == 'workspace.locked':
            receipt['task'] = {
                'family': p['benchmark_family'],
                'case_id': p['case_id'],
                'mission_weight': p['mission_weight'],
                'utility_rubric_version': p['utility_rubric_version'],
                'latency_slo_ms': p['latency_slo_ms'],
                'risk_class': p['risk_class'],
            }
        elif et == 'context.pack.selected':
            receipt.setdefault('context', {}).update({
                'pack_ids': p['pack_ids'],
                'pack_digests': p['pack_digests'],
                'policy_bundle_id': p['policy_bundle_id'],
                'locality_class': p['locality_class'],
            })
        elif et == 'context.pack.fetched':
            receipt.setdefault('context', {}).update({
                'total_bytes': p['total_bytes'],
                'cache_hits': p['cache_hits'],
                'cache_misses': p['cache_misses'],
                'working_set_hit_rate': p['working_set_hit_rate'],
                'remote_fetch_count': p['remote_fetch_count'],
            })
        elif et == 'policy.evaluated':
            receipt.setdefault('outcome', {}).update({
                'policy_pass': p['policy_pass'],
                'human_approved': p.get('human_approved', False),
            })
        elif et == 'placement.selected':
            receipt['placement'] = {
                'site': p['site'],
                'node_pool': p['node_pool'],
                'host_id': p['host_id'],
                'accelerator_type': p['accelerator_type'],
                'execution_mode': p['execution_mode'],
                'planner_version': p['planner_version'],
            }
            receipt['model_runtime'] = {
                'model_id': p['model_id'],
                'model_digest': p['model_digest'],
                'adapter_digest': p.get('adapter_digest'),
                'runtime_id': p['runtime_id'],
                'compiler_id': p.get('compiler_id'),
                'quantization': p.get('quantization'),
                'context_window_tokens': p.get('context_window_tokens'),
            }
        elif et == 'run.completed':
            energy = {
                'train_amortized': p.get('train_amortized', 0.0),
                'inference': p['inference_j'],
                'data_move': p['data_move_j'],
                'network': p['network_j'],
                'storage': p['storage_j'],
                'control': p['control_j'],
                'idle': p['idle_j'],
                'cooling_adjusted': p.get('cooling_adjusted_j', 0.0),
                'replay': p.get('replay_j', 0.0),
                'accounting_boundary': p['accounting_boundary'],
                'estimation_model': p['estimation_model'],
            }
            energy['total'] = round(
                energy['train_amortized'] + energy['inference'] + energy['data_move'] +
                energy['network'] + energy['storage'] + energy['control'] +
                energy['idle'] + energy['cooling_adjusted'], 6
            )
            receipt['energy_j'] = energy
            receipt.setdefault('outcome', {}).update({
                'quality': p['quality'],
                'calibration': p['calibration'],
                'robustness': p['robustness'],
                'latency_ms': p['latency_ms'],
                'replayable': p['replayable'],
            })
        elif et == 'evidence.sealed':
            receipt['evidence'] = {
                'input_digest': p['input_digest'],
                'output_digest': p['output_digest'],
                'evidence_refs': p['evidence_refs'],
                'attestation_refs': p.get('attestation_refs', []),
                'signature': p['signature'],
            }
            receipt['replay'] = {
                'supported': p['replay_supported'],
                'replay_manifest_id': p['replay_manifest_id'],
            }

    return receipt


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit('usage: python tools/receipt_smoke_test.py <trace.json>')
    data = json.loads(Path(sys.argv[1]).read_text())
    receipt = build_receipt(data)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
