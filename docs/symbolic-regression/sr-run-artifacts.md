# PROMETHEUS SR Run Artifacts

Status: v0.1 AgentPlane evidence contract.

AgentPlane records replayable evidence for symbolic-regression discovery runs. It does not admit equations as laws, mutate ontology, authorize policy, or control runtime systems.

## Artifacts

`SRRunArtifact` is the evidence record for a single discovery run.

`SRCandidateRef` is the lightweight candidate reference carried by a run. Candidates can be referenced across runs without duplicating the full run evidence.

## Required integrity posture

`datasetRef` must include both a URI and a SHA-256 content hash. The URI locates the dataset; the content hash makes replay independently verifiable.

`replayHash` is not a UUID. It is a SHA-256 hash of the canonical serialization of covered fields.

Canonical covered-field order:

1. `datasetRef.uri`
2. `datasetRef.contentHash`
3. `methodFamily`
4. `operatorLibrary.binaryOperators` sorted ascending
5. `operatorLibrary.unaryOperators` sorted ascending
6. `operatorLibrary.customOperators` sorted ascending
7. `randomSeed`
8. `runtimeEnvironment.packages` sorted by name ascending, then version
9. `candidateRefs[*].equationLatex` sorted ascending

Canonical serialization is UTF-8 JSON with keys sorted lexicographically and no insignificant whitespace. Any deviation produces a different hash.

## SINDy non-authority

For `methodFamily: sindy`, `controlAuthority` must be `false`. This is machine-readable. A SINDy-derived `PlatformDynamicsCandidate` may describe dynamics but cannot become an autoscaling, routing, remediation, or runtime-control signal from the run artifact alone.

## Random seed

`randomSeed` is required for all methods. It is `null` for deterministic methods and an integer for stochastic methods. It is never absent.

## Runtime environment

At minimum, `runtimeEnvironment.packages` records package names and versions. PySR runs should record both PySR and SymbolicRegression.jl versions when available. SINDy runs should record the PySINDy version.

## Automated gate blocker

Issue #245 defines the still-deferred automated SHACL gate threshold policy. The presence of this run artifact schema does not unblock automated gate production use by itself.
