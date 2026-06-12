"""
WallGuard runtime collaboration and delegation admission gate.

AgentPlane consumes wall context from Agent Registry and policy decisions from
Policy Fabric. It does not implement policy authority locally — it only applies
the gate logic derived from those consumed surfaces.

Gate invariants:
  - Cross-wall: deny before payload exposure (no content written to receipt)
  - Missing wall context: fail closed unconditionally
  - Contaminated session: deny or quarantine; never admit
  - Payload contents are not written into receipts
"""
from __future__ import annotations

from typing import Any

CROSS_WALL_ACTIONS = {
    "agent_message",
    "subagent_delegation",
    "tool_grant",
    "action_dispatch",
    "memory_access",
    "clean_room_handoff",
}

UNKNOWN_SENTINEL = "unknown"


class GateDecision:
    __slots__ = ("admitted", "decision", "reason_code", "wall_outcome", "fail_closed_reason")

    def __init__(
        self,
        *,
        admitted: bool,
        decision: str,
        reason_code: str,
        wall_outcome: str,
        fail_closed_reason: str = "",
    ) -> None:
        self.admitted = admitted
        self.decision = decision
        self.reason_code = reason_code
        self.wall_outcome = wall_outcome
        self.fail_closed_reason = fail_closed_reason


def evaluate(record: dict[str, Any]) -> list[str]:
    """
    Apply gate checks to a WallGuardCollaborationAdmissionReceipt.

    Returns a list of violation strings. Empty list means the record is
    consistent with gate invariants.

    AgentPlane consumes:
      - source_wall_ref / target_wall_ref from Agent Registry wall context
      - wall_decision_outcome from Policy Fabric
      - admitted / admission_decision from the receipt itself

    This function enforces that receipts correctly reflect gate decisions.
    It does not re-evaluate policy; it audits receipt consistency.
    """
    violations: list[str] = []

    source_wall = record.get("source_wall_ref", "")
    target_wall = record.get("target_wall_ref", "")
    admitted = record.get("admitted")
    decision = record.get("admission_decision", "")
    reason_code = record.get("reason_code", "")
    wall_outcome = record.get("wall_decision_outcome", "")

    # Missing wall context must fail closed
    if source_wall == UNKNOWN_SENTINEL or target_wall == UNKNOWN_SENTINEL:
        if admitted or decision != "fail-closed":
            violations.append(
                "missing wall context requires fail-closed non-admission "
                f"(source_wall={source_wall!r}, target_wall={target_wall!r})"
            )
        return violations  # no further checks needed

    # Cross-wall: deny before payload exposure
    if source_wall != target_wall:
        if admitted:
            violations.append(
                f"cross-wall {record.get('collaboration_action')!r} must not be admitted "
                f"(source_wall={source_wall!r}, target_wall={target_wall!r})"
            )
        if reason_code == "same_wall_allowed":
            violations.append(
                "cross-wall collaboration cannot carry reason_code=same_wall_allowed"
            )
        return violations

    # Contaminated session: deny or quarantine, never admit
    if reason_code == "contaminated_session_state":
        if admitted:
            violations.append(
                "contaminated_session_state cannot be admitted; "
                "decision must be deny or require-review"
            )
        if wall_outcome not in ("deny", "quarantine", "escalate"):
            violations.append(
                f"contaminated session requires deny/quarantine/escalate outcome, got {wall_outcome!r}"
            )

    # Same-wall: admitted requires consistent fields
    if admitted:
        if decision != "admit":
            violations.append(
                f"admitted=true requires admission_decision=admit, got {decision!r}"
            )
        if wall_outcome != "allow":
            violations.append(
                f"admitted=true requires wall_decision_outcome=allow, got {wall_outcome!r}"
            )

    return violations
