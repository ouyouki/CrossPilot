"""Approval entity (04 §4.1).

The object is frozen. Once it leaves DRAFT only the columns the design allows
may change (status and the decision bookkeeping); everything a human is agreeing
to is immutable, so "the thing I approved" cannot be edited under the approval
(INV-18). A change of content is a new approval plus SUPERSEDED on the old one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Mapping

from ..core.money import canonical_json, sha256_hex
from ..registry.actions import CONSENT2_ACTION
from .state_machine import ApprovalStatus, assert_transition

#: Fields that may change after DRAFT. Everything else is content.
_MUTABLE_AFTER_DRAFT: frozenset[str] = frozenset(
    {
        "status",
        "version",
        "approver_user_id",
        "approver_kind",
        "delegated_via_grant_id",
        "decided_at",
        "decision_note",
        "void_reasons",
        "successor_id",
        "priority",
        "pending_since",
        "updated_at",
    }
)

_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")

#: Statuses that do not require a human or a grant as the decider.
_NO_DECIDER_STATUSES = frozenset(
    {
        ApprovalStatus.DRAFT,
        ApprovalStatus.PENDING,
        ApprovalStatus.VOID,
        ApprovalStatus.SUPERSEDED,
    }
)


class ApprovalError(ValueError):
    """Programming error on the approval object (not a user-facing problem)."""


def _validate_subject_refs(refs: tuple[str, ...]) -> None:
    if not refs:
        raise ApprovalError("subject_refs must not be empty")
    for ref in refs:
        # 04 §5.2: subject_refs is an id list, never a query condition.
        if not isinstance(ref, str) or not _ID_RE.match(ref):
            raise ApprovalError(f"subject_refs must be ids, got {ref!r}")


def subject_key(refs: tuple[str, ...]) -> str:
    return sha256_hex(canonical_json(sorted(refs)))


@dataclass(frozen=True, slots=True)
class Approval:
    id: str
    shop_id: str
    action_type: str
    status: ApprovalStatus = ApprovalStatus.DRAFT

    # -- content (immutable once PENDING) --------------------------------
    title: str = ""
    subject_refs: tuple[str, ...] = ()
    what_changes: Mapping[str, Any] = field(default_factory=dict)
    why: str = ""
    impact: Mapping[str, Any] = field(default_factory=dict)
    evidence: tuple[Mapping[str, Any], ...] = ()
    alternatives: tuple[Mapping[str, Any], ...] = ()
    recommendation: str = ""
    required_viewed: tuple[str, ...] = ()
    #: Present value of every precondition at creation time, for the diff shown
    #: on the successor approval (04 §5.4).
    preconditions: Mapping[str, Any] = field(default_factory=dict)
    payload_id: str | None = None
    payload_hash: str = ""
    fact_snapshot_id: str = ""
    #: 04 §4.1: the agent that raised the approval; it may never be the approver.
    created_by_agent_id: str | None = None

    # -- decision bookkeeping --------------------------------------------
    approver_user_id: str | None = None
    approver_kind: str | None = None
    delegated_via_grant_id: str | None = None
    decided_at: datetime | None = None
    decision_note: str = ""
    void_reasons: tuple[Mapping[str, Any], ...] = ()
    successor_id: str | None = None
    priority: float = 0.0

    # -- bookkeeping ------------------------------------------------------
    version: int = 1
    created_at: datetime | None = None
    pending_since: datetime | None = None
    updated_at: datetime | None = None

    # -- derived ----------------------------------------------------------
    @property
    def subject_key(self) -> str:
        return subject_key(self.subject_refs)

    @property
    def is_open(self) -> bool:
        from .state_machine import OPEN_STATUSES

        return self.status in OPEN_STATUSES

    # -- construction -----------------------------------------------------
    @classmethod
    def new(
        cls,
        *,
        approval_id: str,
        shop_id: str,
        action_type: str,
        subject_refs: tuple[str, ...],
        now: datetime,
        **content: Any,
    ) -> "Approval":
        _validate_subject_refs(subject_refs)
        payload_hash = content.get("payload_hash", "")
        if action_type == CONSENT2_ACTION and not payload_hash:
            # 04 §4.1: consent 2 freezes the payload when the approval is
            # created; without that hash there is nothing to approve.
            raise ApprovalError("consent 2 must freeze payload_hash at creation")
        return cls(
            id=approval_id,
            shop_id=shop_id,
            action_type=action_type,
            status=ApprovalStatus.DRAFT,
            subject_refs=subject_refs,
            created_at=now,
            updated_at=now,
            **content,
        )

    # -- transitions ------------------------------------------------------
    def transition(self, target: ApprovalStatus, *, now: datetime, **changes: Any) -> "Approval":
        assert_transition(self.status, target)
        if self.status is not ApprovalStatus.DRAFT:
            illegal = set(changes) - _MUTABLE_AFTER_DRAFT
            if illegal:
                raise ApprovalError(
                    "approval content is immutable after DRAFT; open a new approval instead "
                    f"(attempted: {sorted(illegal)})"
                )
        approver = changes.get("approver_user_id", self.approver_user_id)
        grant = changes.get("delegated_via_grant_id", self.delegated_via_grant_id)
        if target not in _NO_DECIDER_STATUSES:
            # INV-4: exactly one of "a named human" and "a grant" must be set.
            # VOID/SUPERSEDED are exempt because the system can void an approval
            # on its own; 06 §7's CHECK omits them, which would make a system
            # VOID impossible — reported as design inconsistency D-2.
            if (approver is None) == (grant is None):
                raise ApprovalError(
                    "approved/executed approvals need exactly one of approver_user_id "
                    "or delegated_via_grant_id"
                )
        if approver is not None and changes.get("approver_kind", self.approver_kind) != "human":
            # No machine signature exists (ADR-13).
            raise ApprovalError("approver must be a human (approver_kind='human')")
        if target is ApprovalStatus.PENDING and self.pending_since is None:
            changes.setdefault("pending_since", now)
        return replace(
            self,
            status=target,
            version=self.version + 1,
            updated_at=now,
            **changes,
        )

    def with_priority(self, priority: float, *, now: datetime) -> "Approval":
        return replace(self, priority=priority, version=self.version + 1, updated_at=now)


__all__ = ["Approval", "ApprovalError", "subject_key"]
