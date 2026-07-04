#!/usr/bin/env python3
"""Model-driven policy — wires a real Claude model as the agent (the production step).

`agent_runtime.AgentRuntime.run_react` drives a loop from a `policy(state) -> action`
callable. Everything downstream (control-flow emission, recovery, narration gating) is
built and tested; the last gap to production was that the policy was a deterministic
stub. `ModelPolicy` closes it: it asks Claude (claude-opus-4-8, adaptive thinking) to
choose the next action via tool use, so the agent's control flow emerges from real model
decisions — and the narration-fidelity gate then verifies the model's own account of what
it did against the recovered structure. A model that misreports its control flow is caught.

The Anthropic client is DEPENDENCY-INJECTED: pass a real `anthropic.Anthropic()` in
production (resolves ANTHROPIC_API_KEY or an `ant auth login` profile) or a scripted fake
in tests — the runtime, recovery, and gate are identical either way. Requires the
`anthropic` SDK only when constructing the default live client; the module itself imports
lazily so the stdlib-only test suite is unaffected.
"""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trace_cfr_reasoning_bridge as bridge  # noqa: E402

MODEL = "claude-opus-4-8"  # default per Anthropic guidance; adaptive thinking on

SYSTEM = (
    "You are an agent that accomplishes a task by calling tools. Choose exactly one "
    "action per turn via the provided tools. Use `call_tool` to act, `loop_guard` to "
    "record a loop-continuation decision (position 'pre' = you checked before the body, "
    "'post' = after), and `finish` when done. Report your control flow honestly: only "
    "claim a loop or branch you actually executed."
)

# The runtime's control-flow primitives, exposed to the model as tools.
ACTION_TOOLS = [
    {
        "name": "call_tool",
        "description": "Execute a tool by name.",
        "input_schema": {
            "type": "object",
            "properties": {"tool": {"type": "string"}, "arg": {"type": "string"}},
            "required": ["tool"],
            "additionalProperties": False,
        },
    },
    {
        "name": "loop_guard",
        "description": "Record a loop-continuation decision after or before the body.",
        "input_schema": {
            "type": "object",
            "properties": {
                "site": {"type": "string", "description": "stable loop-guard site id"},
                "continue_loop": {"type": "boolean"},
                "position": {"type": "string", "enum": ["pre", "post"]},
            },
            "required": ["site", "continue_loop", "position"],
            "additionalProperties": False,
        },
    },
    {
        "name": "finish",
        "description": "Finish the run.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

NARRATE_TOOL = {
    "name": "narrate",
    "description": "State the single top-level control-flow structure you executed for this run.",
    "input_schema": {
        "type": "object",
        "properties": {
            "primitive": {
                "type": "string",
                "enum": ["SEQ", "IF", "IF_ELSE", "WHILE", "DO_WHILE", "SWITCH", "SPAWN_JOIN"],
            },
            "raw": {"type": "string"},
        },
        "required": ["primitive"],
        "additionalProperties": False,
    },
}


def _first_tool_use(response: Any):
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            return block
    return None


class ModelPolicy:
    """A `policy(state) -> action` backed by a Claude model via tool use."""

    def __init__(self, client, model: str = MODEL, system: str = SYSTEM, max_tokens: int = 4096):
        self.client = client
        self.model = model
        self.system = system
        self.max_tokens = max_tokens
        self.messages: list[dict] = []
        self._last_tool_use_id: str | None = None

    def __call__(self, state: dict):
        # feed the previous tool's result back to the model, then ask for the next action
        if self._last_tool_use_id is not None:
            self.messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": self._last_tool_use_id,
                    "content": str(state.get("last_result", "")),
                }],
            })
        elif not self.messages:
            self.messages.append({"role": "user", "content": "Begin the task."})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            system=self.system,
            tools=ACTION_TOOLS,
            tool_choice={"type": "any"},
            messages=self.messages,
        )
        self.messages.append({"role": "assistant", "content": response.content})
        tu = _first_tool_use(response)
        if tu is None:
            return ("done",)
        self._last_tool_use_id = tu.id
        return self._to_action(tu.name, tu.input)

    @staticmethod
    def _to_action(name: str, inp: dict):
        if name == "call_tool":
            return ("tool", inp["tool"], inp.get("arg"))
        if name == "loop_guard":
            taken = "true" if inp["continue_loop"] else "false"
            return ("branch", inp["site"], taken, inp["position"])
        return ("done",)


def narrate_claim(client, events: list[dict], session_id: str = "", model: str = MODEL) -> dict:
    """Ask the model to name the control-flow structure it executed -> a ClaimIR spanning
    the whole run. This is the account the narration-fidelity gate verifies."""
    seg = bridge.reasoning_events_to_segment(events, session_id=session_id)
    covers = [seg["events"][0]["event_id"], seg["events"][-1]["event_id"]]
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system="Report the single top-level control-flow structure you just executed, honestly.",
        tools=[NARRATE_TOOL],
        tool_choice={"type": "tool", "name": "narrate"},
        messages=[{"role": "user", "content": "Narrate the control flow of the run you just completed."}],
    )
    tu = _first_tool_use(response)
    primitive = tu.input["primitive"] if tu else "SEQ"
    raw = (tu.input.get("raw", "") if tu else "")
    return {"claim_id": "model-narration", "covers": covers, "clause": {"primitive": primitive}, "raw": raw}


def default_client():
    """Construct the live Anthropic client (imports the SDK lazily). Resolves credentials
    from ANTHROPIC_API_KEY or an `ant auth login` profile."""
    import anthropic  # noqa: PLC0415

    return anthropic.Anthropic()
