#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("jsonschema is required: python3 -m pip install jsonschema") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REQUEST = ROOT / "schemas" / "rollback-restore-request.schema.v0.1.json"
SCHEMA_RECEIPT = ROOT / "schemas" / "rollback-restore-receipt.schema.v0.1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "rollback-restore"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    return data


def schema_for(data: dict[str, Any], schemas: dict[str, Any]) -> dict[str, Any]:
    kind = data.get("kind", "")
    if kind == "RollbackRestoreRequest":
        return schemas["request"]
    if kind == "RollbackRestoreReceipt":
        return schemas["receipt"]
    raise ValueError(f"unknown kind: {kind}")


def check_policy_gates(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    kind = data.get("kind")

    if kind == "RollbackRestoreRequest":
        authority_state = data.get("authority_state", "")
        if authority_state in ("suspended", "revoked"):
            problems.append(
                f"authority_state={authority_state!r}; restore requires active authority"
            )

        safe_root = data.get("safe_root", "")
        for path in data.get("restore_target_paths", []):
            if not path.startswith(safe_root):
                problems.append(
                    f"path escape: {path!r} is not under safe_root {safe_root!r}"
                )

    if kind == "RollbackRestoreReceipt":
        if data.get("restore_status") == "completed":
            if not data.get("before_digest_verified"):
                problems.append(
                    "restore_status=completed requires before_digest_verified=true"
                )
            if not data.get("after_digest_verified"):
                problems.append(
                    "restore_status=completed requires after_digest_verified=true"
                )

    if not data.get("non_claims"):
        problems.append("non_claims must not be empty")

    return problems


def validate_file(path: Path, schemas: dict[str, Any]) -> list[str]:
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"parse error: {exc}"]
    try:
        schema = schema_for(data, schemas)
        jsonschema.validate(data, schema)
    except (jsonschema.ValidationError, ValueError) as exc:
        return [f"schema: {exc}"]
    return check_policy_gates(data)


def main() -> int:
    schemas = {
        "request": load_json(SCHEMA_REQUEST),
        "receipt": load_json(SCHEMA_RECEIPT),
    }
    failed = False

    valids = sorted(FIXTURES.glob("valid.*.json"))
    if not valids:
        raise SystemExit("missing valid rollback-restore fixtures")

    for path in valids:
        problems = validate_file(path, schemas)
        if problems:
            print(f"FAIL (valid): {path.name}")
            for p in problems:
                print(f"  - {p}")
            failed = True
        else:
            print(f"ok: {path.name}")

    rejects = sorted(FIXTURES.glob("reject.*.json"))
    if not rejects:
        raise SystemExit("missing reject rollback-restore fixtures")

    for path in rejects:
        problems = validate_file(path, schemas)
        if not problems:
            print(f"FAIL (reject should have failed): {path.name}")
            failed = True
        else:
            print(f"ok (rejected as expected): {path.name}")

    print(
        ("PASS" if not failed else "FAIL")
        + f": rollback restore — {len(valids)} valid, {len(rejects)} reject"
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
