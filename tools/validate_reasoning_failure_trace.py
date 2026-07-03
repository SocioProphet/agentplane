#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "reasoning-failure-trace.schema.v0.1.json"
EXAMPLE = ROOT / "examples" / "reasoning-failure-trace.exact-string.json"
ONTOLOGY_PREFIX = "https://socioprophet.github.io/ontogenesis/platform/reasoning-failure#"


def fail(message: str) -> int:
    print(f"ERR: {message}", file=sys.stderr)
    return 2


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    try:
        for path in (SCHEMA, EXAMPLE):
            if not path.exists():
                raise FileNotFoundError(path)

        schema = load_json(SCHEMA)
        example = load_json(EXAMPLE)

        require(schema.get("title") == "AgentPlane ReasoningFailureTrace v0.1", "schema title mismatch")
        require(example.get("kind") == "ReasoningFailureTrace", "example.kind must be ReasoningFailureTrace")
        require(example.get("version") == "0.1", "example.version must be 0.1")

        missing = [field for field in schema.get("required", []) if field not in example]
        require(not missing, f"example missing schema-required fields: {missing}")

        failure_refs = example["failureModeRefs"]
        require(failure_refs, "failureModeRefs must not be empty")
        require(all(ref.startswith(ONTOLOGY_PREFIX) for ref in failure_refs), "failureModeRefs must use Ontogenesis refs")

        verifier = example["verifier"]
        require(verifier["required"] is True, "exactness trace must require verifier")
        require(verifier["verifierFamily"] == "deterministic", "exactness trace must use deterministic verifier")
        require(verifier["result"] == "failed", "bootstrap example must represent a failed verifier")

        checks = example["invariantChecks"]
        require(checks and checks[0]["passed"] is False, "bootstrap example must include failed invariant check")
        require(checks[0]["expected"] != checks[0]["observed"], "failed invariant must preserve mismatch evidence")

        termination = example["termination"]
        require(termination["candidateStatus"] == "premature-candidate", "failed verifier must mark premature candidate")
        require(termination["finalStatus"] == "needs-review", "failed verifier must require review")

        annotations = example["annotations"]
        require(annotations, "annotations must not be empty")
        require(
            any(a["cluster"] == "task-verification-termination" for a in annotations),
            "trace must include task-verification-termination annotation",
        )
        require(
            all(a["failureModeRef"].startswith(ONTOLOGY_PREFIX) for a in annotations),
            "annotation failureModeRef values must use Ontogenesis refs",
        )

        require(example["riskAction"] == "require-tool-verification", "exactness trace must require tool verification")
        require(example["evidenceRefs"], "evidenceRefs must not be empty")
    except FileNotFoundError as exc:
        return fail(f"missing required file: {exc.args[0]}")
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))

    print("OK: validated reasoning failure trace schema and exactness fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
