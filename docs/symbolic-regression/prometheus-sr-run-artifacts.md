# PROMETHEUS SR Run Artifacts

Status: v0.1 AgentPlane evidence contract.

AgentPlane records replayable evidence for symbolic-regression discovery runs. It does not admit equations as laws, mutate ontology, authorize policy, or control runtime systems.

`SRRunArtifact` is the evidence record for a single discovery run. `SRCandidateRef` is the lightweight candidate reference carried by a run. Candidates can be referenced across runs without duplicating the full run evidence.

`datasetRef` must include both a URI and a SHA-256 content hash. The URI locates the dataset; the content hash makes replay independently verifiable.

`replayHash` is not a UUID. It is a SHA-256 hash of the canonical serialization of covered fields.

Canonical covered-field order: datasetRef.uri, datasetRef.contentHash, methodFamily, operatorLibrary.binaryOperators sorted ascending, operatorLibrary.unaryOperators sorted ascending, operatorLibrary.customOperators sorted ascending, randomSeed, runtimeEnvironment.packages sorted by package name ascending then version, and candidateRefs[*].equationLatex sorted ascending.

Canonical serialization is UTF-8 JSON with keys sorted lexicographically and no insignificant whitespace. Any deviation produces a different hash.

For methodFamily `sindy`, controlAuthority must be false. This is a machine-readable non-authority guarantee. A SINDy-derived PlatformDynamicsCandidate may describe dynamics but cannot become an autoscaling, routing, remediation, or runtime-control signal from the run artifact alone.

`randomSeed` is required for all methods. It is null for deterministic methods and an integer for stochastic methods. It is never absent.

At minimum, `runtimeEnvironment.packages` records package names and versions. PySR runs should record both PySR and SymbolicRegression.jl versions when available. SINDy runs should record the PySINDy version.

Issue #245 defines the still-deferred automated SHACL gate threshold policy. The presence of this run artifact schema does not unblock automated gate production use by itself.
