"""Decision vocabulary of the Gatekeeper (04 §3.1).

Exactly four outcomes exist. There is deliberately no "unknown" member: an
engine that cannot decide must return ``HOLD``, because INV-9 forbids ALLOW as
the result of a degraded decision (fail-closed by shape, not by convention).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW_AUTO = "ALLOW_AUTO"
    REQUIRE_HUMAN = "REQUIRE_HUMAN"
    BLOCK = "BLOCK"
    HOLD = "HOLD"


class Disposition(str, Enum):
    """Registry disposition (04 §2).

    ``NEVER`` exists only so tests can assert its absence from the registry:
    a NEVER action must not be registered at all (04 §2.2, INV-12).
    """

    AUTO = "AUTO"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    HUMAN_INITIATED = "HUMAN_INITIATED"
    NEVER = "NEVER"


class Reversibility(str, Enum):
    REVERSIBLE = "REVERSIBLE"
    COMPENSABLE = "COMPENSABLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class Severity(str, Enum):
    BLOCK = "BLOCK"
    WARN = "WARN"


class Tri(str, Enum):
    """Three-valued rule evaluation (04 §3.2).

    ``UNKNOWN`` is *not* "no match": a rule whose required fact is missing must
    push the action to HOLD instead of being treated as not triggered (INV-20).
    """

    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Reason:
    """One evaluable explanation attached to a verdict (04 §3.1)."""

    rule_id: str
    severity: Severity
    message: str = ""
    rule_version: str = ""
    hit_text: str | None = None
    facts: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Verdict:
    decision: Decision
    reasons: tuple[Reason, ...] = ()
    missing_facts: tuple[str, ...] = ()
    ruleset_version: str = ""
    #: True when the verdict came from a HUMAN_INITIATED click rather than from
    #: an autonomous decision. The Tool Gate uses it only for auditing.
    human_initiated: bool = False

    @property
    def is_blocked(self) -> bool:
        return self.decision is Decision.BLOCK

    @property
    def is_held(self) -> bool:
        return self.decision is Decision.HOLD
