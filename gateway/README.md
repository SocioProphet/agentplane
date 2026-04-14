# gateway

Tenant ingress for policy-scoped remote work.

Initial responsibilities:

- accept remote-eligible work only after policy approval upstream
- validate capability binding requests
- reject side-effecting or out-of-policy execution attempts
- emit tenant-side evidence relay events

This directory is a scaffold for the first local-hybrid slice and should stay narrow until the typed execution path is implemented.
