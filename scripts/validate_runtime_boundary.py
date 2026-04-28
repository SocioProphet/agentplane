#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def die(msg: str, code: int = 2) -> None:
    print(f"[runtime-boundary] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load(path: str):
    if not os.path.exists(path):
        die(f"file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            die(f"invalid JSON in {path}: {exc}")


def check_osimage(doc: dict) -> list[str]:
    failures = []
    for forbidden in ('deploymentEnvironmentName', 'serviceIdentity', 'policyRefs', 'relations', 'objectives'):
        if forbidden in doc:
            failures.append(f'OSImage contains forbidden runtime field: {forbidden}')
    for forbidden in ('topology', 'region', 'site', 'customer', 'fleet'):
        if forbidden in doc:
            failures.append(f'OSImage contains forbidden mutable field: {forbidden}')
    short_id = str(doc.get('shortId', '')).lower()
    for token in ('dev', 'stage', 'staging', 'prod', 'production', 'sensor', 'planner', 'governor', 'auditor'):
        if token and token in short_id:
            failures.append(f'OSImage.shortId leaks forbidden token: {token}')
    return failures


def check_nodebinding(doc: dict) -> list[str]:
    failures = []
    for forbidden in ('osRelease', 'ociAnnotations', 'substrateCapabilities', 'provenance'):
        if forbidden in doc:
            failures.append(f'NodeBinding redefines substrate-only field: {forbidden}')
    return failures


def check_cybernetic(doc: dict) -> list[str]:
    failures = []
    for forbidden in ('osRelease', 'ociAnnotations', 'substrateCapabilities', 'provenance'):
        if forbidden in doc:
            failures.append(f'CyberneticAssignment contains substrate-only field: {forbidden}')
    return failures


def main() -> int:
    if len(sys.argv) != 4:
        die('usage: scripts/validate_runtime_boundary.py <osimage.json> <nodebinding.json> <cyberneticassignment.json>')

    osimage = load(sys.argv[1])
    nodebinding = load(sys.argv[2])
    cyber = load(sys.argv[3])

    failures = []
    if osimage.get('type') != 'OSImage':
        failures.append('first input must be type=OSImage')
    else:
        failures.extend(check_osimage(osimage))

    if nodebinding.get('type') != 'NodeBinding':
        failures.append('second input must be type=NodeBinding')
    else:
        failures.extend(check_nodebinding(nodebinding))

    if cyber.get('type') != 'CyberneticAssignment':
        failures.append('third input must be type=CyberneticAssignment')
    else:
        failures.extend(check_cybernetic(cyber))

    if failures:
        print(json.dumps({'status': 'fail', 'failures': failures}, indent=2))
        return 1

    report = {
        'status': 'pass',
        'osImageRef': osimage.get('id'),
        'nodeBindingRef': nodebinding.get('id'),
        'cyberneticAssignmentRef': cyber.get('id'),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
