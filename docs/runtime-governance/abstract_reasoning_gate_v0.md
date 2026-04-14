# Abstract reasoning gate v0

## Status

Patch/spec note for the next runtime enforcement cut.

This note records the abstract-reasoning gate semantics that Agentplane should enforce during bundle validation before execution proceeds.

## Why this exists

The current control-gate flow already evaluates lane, authority, environment tier, approval mode, tenant scope, and enforcement point.

That is not sufficient for abstract or program-induction work.

A branch in the abstract lane may produce:
- a plausible answer,
- a plausible rationale,
- compilable code,

and still fail to recover the governing rule.

Therefore Agentplane needs an additional posture check for abstract work before execution eligibility.

## Intended bundle policy shape

`spec.policy.abstractReasoning` should support at least:

- `reasoningClass`
- `verificationMode`
- `llmOnlyForbidden`
- `requiresCounterexampleSearch`
- `requiresProgramCandidate`
- `requiresBacktrackingCapability`
- `programCandidateRef`
- `counterexampleRefs`
- `backtrackingCapable`

## Intended gate behavior

When `reasoningClass` is `ABSTRACT` or `PROGRAM_INDUCTION`:

1. deny the bundle if `llmOnlyForbidden=true` and `verificationMode=NONE`
2. deny the bundle if `requiresProgramCandidate=true` and `programCandidateRef` is missing
3. deny the bundle if `requiresCounterexampleSearch=true` and `counterexampleRefs` is empty
4. deny the bundle if `requiresBacktrackingCapability=true` and `backtrackingCapable=false`

## Intended artifact impact

`ControlGateArtifact.gateContext` should expose the abstract-reasoning posture fields.

`ValidationArtifact` should expose an `abstractGate` section summarizing:
- reasoning class
- verification mode
- llm-only prohibition
- counterexample requirement
- program-candidate requirement
- backtracking-capability requirement

## Non-goal

This note does not change execution artifacts yet.
It only records the validation-time gate behavior needed to make the abstract lane enforceable.
