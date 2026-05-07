# Execution Evidence Runner Cleanup v0

## Status

Draft follow-up to the postcondition/divergence evidence tranche.

## Purpose

AgentPlane now has typed postcondition and divergence evidence contracts. Runner paths should call evidence emitters instead of writing canonical JSON inline.

## Current problem

`runners/qemu-local.sh` still contains inline JSON emission for some canonical runtime artifacts. Inline shell JSON makes drift likely when schemas evolve.

## Cleanup rule

Shell runners may orchestrate execution, copy artifacts, and pass arguments.

Python emitters own canonical artifact shape.

## Intended path

1. Land postcondition/divergence schemas and narrow emitters.
2. Add `scripts/emit_execution_evidence_artifacts.py` as the runner-facing wrapper.
3. Update runner paths to call the wrapper after `run-artifact.json` exists.
4. Remove inline canonical postcondition/divergence JSON from runner code.
5. Later, reduce remaining inline run/replay emission where dedicated emitters already exist.

## Initial runner-facing command shape

```bash
python3 scripts/emit_execution_evidence_artifacts.py \
  path/to/bundle.json \
  agentplane://run-artifact/run-artifact.json \
  --expected-state-hash "$PLANNER_EXPECTED_STATE_HASH" \
  --observed-state-hash "$OBSERVED_STATE_HASH" \
  --comparison-result "$POSTCONDITION_RESULT"
```

When divergence exists:

```bash
python3 scripts/emit_execution_evidence_artifacts.py \
  path/to/bundle.json \
  agentplane://run-artifact/run-artifact.json \
  --expected-state-hash "$PLANNER_EXPECTED_STATE_HASH" \
  --observed-state-hash "$OBSERVED_STATE_HASH" \
  --comparison-result FAIL \
  --divergence-class ABSTRACTION_FAILURE \
  --expected-ref "$EXPECTED_REF" \
  --observed-ref "$OBSERVED_REF" \
  --replan-required
```

## Non-goals

- Do not rewrite `qemu-local.sh` wholesale in the same tranche.
- Do not change SourceOS image-production validation.
- Do not change run/replay schemas in this first cleanup pass.

## Acceptance

The first cleanup tranche is acceptable when:

- the wrapper exists;
- the wrapper delegates to the narrow emitters;
- mismatch results require divergence metadata;
- runner integration is documented before shell mutation begins.
