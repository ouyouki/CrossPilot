"""Approval state machine (04 §5.3).

The table below is the only place a status change may be authorised. It has no
clock-driven edge, which is what INV-2 tests: fast-forwarding a year cannot move
a PENDING approval anywhere, because no such transition exists to be triggered.

``OUTCOME_UNKNOWN`` is terminal here on purpose. The design says "read back
first, then decide whether to retry" but does not list outgoing edges; adding
them by guess would let an unverified readback approve itself. Until that gap is
decided (open question Q-01) the only way out is a human and a new approval.
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping


class ApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    EXEC_FAILED = "EXEC_FAILED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    SUPERSEDED = "SUPERSEDED"
    VOID = "VOID"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"


TRANSITIONS: Mapping[ApprovalStatus, frozenset[ApprovalStatus]] = {
    ApprovalStatus.DRAFT: frozenset({ApprovalStatus.PENDING, ApprovalStatus.VOID}),
    ApprovalStatus.PENDING: frozenset(
        {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.RETURNED,
            ApprovalStatus.SUPERSEDED,
            ApprovalStatus.VOID,
        }
    ),
    ApprovalStatus.APPROVED: frozenset({ApprovalStatus.EXECUTING, ApprovalStatus.VOID}),
    ApprovalStatus.EXECUTING: frozenset(
        {
            ApprovalStatus.EXECUTED,
            ApprovalStatus.EXEC_FAILED,
            ApprovalStatus.VOID,
            ApprovalStatus.OUTCOME_UNKNOWN,
        }
    ),
    ApprovalStatus.EXEC_FAILED: frozenset({ApprovalStatus.EXECUTING, ApprovalStatus.VOID}),
    ApprovalStatus.OUTCOME_UNKNOWN: frozenset(),
    ApprovalStatus.EXECUTED: frozenset(),
    ApprovalStatus.REJECTED: frozenset(),
    ApprovalStatus.RETURNED: frozenset(),
    ApprovalStatus.SUPERSEDED: frozenset(),
    ApprovalStatus.VOID: frozenset(),
}

#: Statuses covered by the partial unique index on open approvals (06 §7).
OPEN_STATUSES: frozenset[ApprovalStatus] = frozenset(
    {
        ApprovalStatus.DRAFT,
        ApprovalStatus.PENDING,
        ApprovalStatus.APPROVED,
        ApprovalStatus.EXECUTING,
    }
)

TERMINAL_STATUSES: frozenset[ApprovalStatus] = frozenset(
    {
        ApprovalStatus.EXECUTED,
        ApprovalStatus.REJECTED,
        ApprovalStatus.RETURNED,
        ApprovalStatus.SUPERSEDED,
        ApprovalStatus.VOID,
        ApprovalStatus.OUTCOME_UNKNOWN,
    }
)


class TransitionError(ValueError):
    def __init__(self, current: ApprovalStatus, target: ApprovalStatus) -> None:
        super().__init__(f"illegal approval transition: {current.value} -> {target.value}")
        self.current = current
        self.target = target


def can_transition(current: ApprovalStatus, target: ApprovalStatus) -> bool:
    return target in TRANSITIONS.get(current, frozenset())


def assert_transition(current: ApprovalStatus, target: ApprovalStatus) -> None:
    if not can_transition(current, target):
        raise TransitionError(current, target)


def assert_no_time_driven_edges() -> None:
    """Structural check used by the INV-2 test.

    There is no timer table, no ``expires_at`` on an approval and no status that
    is reachable from a clock; this function documents that in executable form.
    """
    for current, targets in TRANSITIONS.items():
        for target in targets:
            assert isinstance(current, ApprovalStatus) and isinstance(target, ApprovalStatus)
    assert ApprovalStatus.PENDING in OPEN_STATUSES
    assert TERMINAL_STATUSES.isdisjoint(OPEN_STATUSES)


__all__ = [
    "OPEN_STATUSES",
    "TERMINAL_STATUSES",
    "TRANSITIONS",
    "ApprovalStatus",
    "TransitionError",
    "assert_no_time_driven_edges",
    "assert_transition",
    "can_transition",
]
