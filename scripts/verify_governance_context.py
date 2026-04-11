#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import jsonschema


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    schema_root = root / 'schemas'
    bundle_schema = load(schema_root / 'bundle.schema.v0.1.json')
    gc_schema = load(schema_root / 'governance-context.schema.v0.1.json')
    bundle = load(root / 'bundles' / 'example-agent' / 'bundle.json')
    gc = load(root / 'examples' / 'governance' / 'governance-context.example.json')
    resolver_store = {
        'governance-context.schema.v0.1.json': gc_schema,
        (schema_root / 'governance-context.schema.v0.1.json').as_uri(): gc_schema,
    }
    jsonschema.validate(gc, gc_schema)
    jsonschema.Draft202012Validator(
        bundle_schema,
        resolver=jsonschema.RefResolver.from_schema(bundle_schema, store=resolver_store),
    ).validate(bundle)
    print('[verify-governance] OK: example governance context and bundle validate')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
