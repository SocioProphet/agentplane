# Control-plane contract linkage

`agentplane` is the execution and promotion control-plane home, but it is not the shared schema canon.

## Shared contract references

The shared schema and vocabulary canon for reusable control-plane terms belongs in:

- `SocioProphet/socioprophet-agent-standards`

Initial shared terms referenced by this repository:

- channel (`dev`, `candidate`, `stable`)
- capability definition

## Repository relationship

- `agentplane` defines the execution lifecycle and evidence flow.
- `socioprophet-agent-standards` defines the shared schema and vocabulary layer.
- `source-os` realizes Linux hosts, images, and builders that participate in the control plane.

## Practical rule

When this repository needs a reusable cross-repo term, the durable schema or vocabulary definition should be added to `socioprophet-agent-standards` and then referenced here, rather than silently redefining the term locally.
