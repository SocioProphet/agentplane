# capability-registry

Logical capability descriptors and runtime bindings live here.

Initial responsibilities:

- map capability IDs to execution bindings
- record execution-lane constraints
- record timeout and context limits
- record side-effect posture and credential scope requirements

The first concrete example to support is a narrow capability such as `summarize.abstractive.v1`.
