# OrderDescriptor to Bundle bridge v0.1

## Purpose

This note defines the narrow mapping from commons governed work into agentplane execution.

## Principle

`agentplane` remains the execution control plane.
It does not become the source of truth for knowledge taxonomy, content spaces, or publication semantics.

## Mapping

- `OrderDescriptor.metadata.id` -> execution metadata reference
- `OrderDescriptor.spec.policy.policyPackRef` -> `Bundle.spec.policy.policyPackRef`
- `OrderDescriptor.spec.policy.policyPackHash` -> `Bundle.spec.policy.policyPackHash`
- `OrderDescriptor.spec.validation.humanGateRequired` -> `Bundle.spec.policy.humanGateRequired`
- `OrderDescriptor.spec.validation.maxRunSeconds` -> `Bundle.spec.policy.maxRunSeconds`

## Evidence linking

When execution occurs, emitted artifacts SHOULD preserve:
- `orderId`
- target `descriptorId`
- upstream evidence refs when available

## Constraint

The full `GeneralDescriptor` MUST NOT be copied into the bundle.
Only execution-relevant fields, stable ids, and evidence references should cross the bridge.
