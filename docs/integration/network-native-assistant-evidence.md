# Network Door, External Model Provider, and Native Assistant evidence

AgentPlane owns evidence contracts for governed execution and replay. This integration note defines the evidence seam for the SourceOS Network Door, BYOM/external model-provider routing, and Native Assistant Door plan surfaces.

These schemas are intentionally evidence-only. They do not install firewalls, mutate mesh state, contact model providers, invoke native assistants, download model weights, or send prompts.

## Evidence schemas

| Schema | Kind | Source command surface |
|---|---|---|
| `schemas/network-door-plan-evidence.schema.v0.1.json` | `NetworkDoorPlanEvidence` | `sourceosctl network doctor`, `sourceosctl network plan`, `sourceosctl network evidence inspect` |
| `schemas/external-model-provider-route-evidence.schema.v0.1.json` | `ExternalModelProviderRouteEvidence` | `sourceosctl network provider` and future model-router BYOM route adapters |
| `schemas/native-assistant-bridge-evidence.schema.v0.1.json` | `NativeAssistantBridgeEvidence` | `sourceosctl native-assistant plan` and future native bridge adapters |

## Contract refs

The schemas reference SourceOS contract concepts from `SourceOS-Linux/sourceos-spec`:

- `NetworkAccessProfile`
- `FirewallBindingProfile`
- `MeshBindingProfile`
- `ExternalModelProviderProfile`
- `NativeAssistantBridgeProfile`

AgentPlane records those refs and policy posture. It does not redefine those contracts.

## Required posture

### Network Door

Network Door evidence records:

- network access profile refs;
- user and enterprise firewall binding refs;
- optional mesh binding refs;
- BYOM/external model provider refs;
- hash-only destination evidence;
- route decision and scope;
- enterprise/user precedence posture;
- side-effect flags proving whether firewall or mesh state was mutated.

The default posture is non-mutating. Firewall and mesh bindings are complementary controls; one should not be treated as a substitute for the other.

### External model provider route

External model provider evidence records:

- provider ref and provider class;
- owner: user, enterprise, workspace, tenant, or device;
- network, firewall, mesh, and model-router binding refs;
- endpoint/auth references without inline credentials;
- prompt hash-only evidence;
- prompt egress policy;
- provider health metadata only when explicitly checked;
- side-effect flags proving whether a provider was contacted or a prompt was sent.

Credentials must remain references. Do not inline tokens, API keys, endpoints containing credentials, or secret material in evidence.

### Native Assistant Door

Native Assistant evidence records:

- bridge refs for Apple App Intents/Siri/Shortcuts, Android intents, Windows shell, browser extensions, MCP, or other host/device bridge classes;
- operation being planned or executed;
- prompt hash-only evidence;
- user confirmation posture;
- network/model-router/agent-registry refs;
- policy posture for prompt egress, personal context reads, cross-device handoff, side effects, and raw app database access;
- side-effect flags proving whether a native assistant/app action actually occurred.

Native assistant evidence should default to non-mutating plans. Real assistant invocation, reminder/note creation, sharing, cross-device handoff, or personal context reads must be explicit policy-gated side effects.

## Import path

The first import path is from `sourceosctl` plan surfaces:

```text
sourceosctl network ...             -> NetworkDoorPlanEvidence / ExternalModelProviderRouteEvidence
sourceosctl native-assistant plan   -> NativeAssistantBridgeEvidence
```

Future import paths:

```text
model-router BYOM route             -> ExternalModelProviderRouteEvidence
AgentTerm /network                  -> NetworkDoorPlanEvidence event refs
AgentTerm /native-assistant         -> NativeAssistantBridgeEvidence event refs
Guardrail Fabric policy decision    -> policyRefs / policyHash
```

## Non-goals

- Do not mutate firewall rules from these evidence contracts.
- Do not install Istio, Admiral, Linkerd, Cilium, or enterprise mesh components from these evidence contracts.
- Do not contact external/BYOM model providers unless an executor adapter explicitly performs a policy-approved health check or route.
- Do not invoke native assistant APIs from evidence creation.
- Do not store prompt text, destination text, credentials, or secrets in evidence records.
- Do not expose raw Apple Notes, Photos, mail stores, browser profiles, keychains, token stores, or other raw host app databases by default.
