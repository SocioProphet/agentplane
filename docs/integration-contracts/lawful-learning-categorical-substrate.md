# Lawful-learning categorical substrate for Phase 9 receipts

**Status:** v1 doctrine substrate.

**Date:** May 13, 2026

**Scope:** Defines the categorical substrate AgentPlane uses when receiving lawful-learning evidence receipts. This document is consumed by `lawful-learning-phase9-contract.md` and the Phase 9 receipt classes.

**Boundary:** This substrate is a semantics and schema discipline. It does not add runtime verification, cryptographic authenticity, cross-plane evidence resolution, or truth-annealing execution.

## 1. Canonical adjacency

Phase 9 uses the standard 10-state / 22-edge adjacency with Da'at not modeled as an eleventh node.

The node basis is:

```text
K   Keter      telos / objective
C   Chokhmah   hypothesis / exploration
B   Binah      model / formal structure
Cp  Chesed     accept / adopt operator
G   Gevurah    reject / rigor operator
T   Tiferet    reconcile / mediate operator
N   Netzach    persist / execute
H   Hod        interpret / communicate
Y   Yesod      integrate / ledger
M   Malkhut    manifest / output
```

The edge basis is:

```text
E01 K-C
E02 K-B
E03 K-T
E04 C-B
E05 C-T
E06 C-Cp
E07 B-T
E08 B-G
E09 Cp-G
E10 Cp-T
E11 Cp-N
E12 G-T
E13 G-H
E14 T-N
E15 T-Y
E16 T-H
E17 N-H
E18 N-Y
E19 N-M
E20 H-Y
E21 H-M
E22 Y-M
```

Phase 9 receipt classes may reference `edge_contract_ref` values in this edge basis.

## 2. Da'at as factorization, not node

Da'at is modeled as categorical factorization, not as a separate receipt state.

```text
K --E03--> T = K -> D_up -> D_down -> T
```

`D_up` is the equalizer-like higher-knowledge structure on the hypothesis/model round trip. `D_down` is the operational interface into legitimacy and execution. Receipt schemas do not add a Da'at node. They may reference `daat_factorization` in doctrine notes, but no runtime field may use Da'at as an additional state object.

## 3. Ω truth codomain

Phase 9 uses the seven-value truth codomain derived from the subobject classifier of directed multigraphs:

```text
F_v       vertex out
T_v       vertex in
bottom_e  edge absent / no endpoint anchor
sigma_hat source anchored only
tau_hat   target anchored only
partial   both endpoints supported, no integrating chain
top_e     fully validated traversal declared
```

The value `partial` is intentionally distinct from `top_e`: endpoint support is not equivalent to full traversal membership.

## 4. Truth records

A Phase 9 lawful-learning receipt may carry a `truth_record` object.

A `truth_record` records:

```text
omega_value             one of the seven Ω values
sieve_state             provenance-closure state that justifies omega_value
edge_contract_ref       optional E01-E22 edge contract reference
provenance_refs         opaque evidence/provenance references
adversary_model_refs    optional declared adversary model references
```

AgentPlane validates the shape of `truth_record`. It does not execute truth annealing and does not semantically verify the truth value.

## 5. Policy threshold separation

The telos/policy layer may define an acceptance threshold `policy_threshold_ref`, corresponding to θ(C), but it must not write into `truth_record.omega_value`.

Legal coupling:

```text
accepted_for_action iff omega_value >= policy_threshold_ref
```

Illegal coupling:

```text
policy writes truth_record.omega_value
policy overwrites provenance sieve state
policy claims top_e without full traversal evidence
```

The Phase 9 checker rejects receipts that include policy-overwrite fields.

## 6. Sieve/provenance interpretation

A truth value is interpreted as a sieve over admissible provenance morphisms. AgentPlane's v1 contract only records this interpretation; it does not compute closure.

Canonical readings:

```text
bottom_e  no valid evidence chain
sigma_hat artifact-side evidence only
tau_hat   witness-side evidence only
partial   both endpoints supported, no validated chain
top_e     declared full traversal exists
```

## 7. Edge-contract bootstrap

The first populated edge contracts available for reference are:

```text
E04  Chokhmah-Binah    hypothesis <-> model
E12  Gevurah-Tiferet   rejection <-> reconciliation
E18  Netzach-Yesod     persistence <-> integration
```

Additional edge contracts may be introduced later. Phase 9 receipt schemas allow any E01-E22 reference so future edge-contract population does not require schema changes.

## 8. Non-claims

This substrate does not claim:

```text
runtime truth annealing
computed Grothendieck topology closure
semantic truth verification
Da'at as a runtime node
policy authority to mutate truth_record.omega_value
complete edge-contract library
cross-plane evidence resolution
```
