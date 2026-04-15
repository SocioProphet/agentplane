# worker-runtime

Tenant worker execution wrappers and contract adapters live here.

Initial responsibilities:

- accept only typed capability payloads
- run with scoped credentials
- record input and output digests
- emit provenance metadata for evidence append

This directory should remain tightly bounded to the first local-hybrid slice until the typed execution path is verified end to end.
