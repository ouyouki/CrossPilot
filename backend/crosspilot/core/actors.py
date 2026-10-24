"""Who is calling the Tool Gate.

The design has exactly three actor kinds (04 §12): a human, an agent, and the
system itself (worker/scheduler). Keeping them as one value object makes the
"no machine signature" rule (ADR-13, INV-4) a type-level fact rather than a
comment.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ToolGateError
from ..registry.actions import ROLES

HUMAN = "human"
AGENT = "agent"
SYSTEM = "system"
_ACTOR_KINDS = frozenset({HUMAN, AGENT, SYSTEM})


@dataclass(frozen=True, slots=True)
class Actor:
    kind: str
    id: str
    role: str | None = None
    agent_name: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in _ACTOR_KINDS:
            raise ToolGateError("ACTION_FORBIDDEN", f"unknown actor kind: {self.kind!r}")
        if not self.id:
            raise ToolGateError("ACTION_FORBIDDEN", "actor id is required")
        if self.kind == HUMAN:
            if self.role not in ROLES:
                raise ToolGateError("ACTION_FORBIDDEN", f"human without a valid role: {self.role!r}")
        if self.kind == AGENT and not self.agent_name:
            raise ToolGateError("ACTION_FORBIDDEN", "agent actor needs agent_name")

    @classmethod
    def human(cls, user_id: str, role: str) -> "Actor":
        return cls(kind=HUMAN, id=user_id, role=role)

    @classmethod
    def agent(cls, name: str) -> "Actor":
        return cls(kind=AGENT, id=f"agent:{name}", agent_name=name)

    @classmethod
    def system(cls, name: str = "worker") -> "Actor":
        return cls(kind=SYSTEM, id=f"system:{name}")


__all__ = ["AGENT", "Actor", "HUMAN", "SYSTEM"]
