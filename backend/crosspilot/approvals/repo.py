"""In-memory approval repository with the DB-level guards of 06 §7, restated.

The real store is PostgreSQL; this one exists so the engine's invariants are
testable without a database, and it implements the same three guards:

* one open approval per (shop, action, subject),
* content cannot be overwritten without a version bump,
* execution start is a compare-and-set from APPROVED -> EXECUTING (INV-17).

When the SQL layer lands, these stay as the application-side checks and the
constraints become the second line of defence.
"""

from __future__ import annotations

import threading
from typing import Iterable

from ..core.errors import ToolGateError
from .model import Approval
from .state_machine import OPEN_STATUSES, ApprovalStatus


class ApprovalRepo:
    """Protocol-ish base class; the SQL implementation must match it."""

    def add(self, approval: Approval) -> Approval:  # pragma: no cover - interface
        raise NotImplementedError

    def get(self, approval_id: str) -> Approval:  # pragma: no cover - interface
        raise NotImplementedError

    def save(self, approval: Approval) -> Approval:  # pragma: no cover - interface
        raise NotImplementedError

    def try_begin_execution(self, approval_id: str, *, now) -> Approval:  # pragma: no cover
        raise NotImplementedError


class InMemoryApprovalRepo(ApprovalRepo):
    def __init__(self) -> None:
        self._items: dict[str, Approval] = {}
        self._lock = threading.RLock()

    # -- queries ----------------------------------------------------------
    def get(self, approval_id: str) -> Approval:
        try:
            return self._items[approval_id]
        except KeyError as exc:
            raise KeyError(f"approval not found: {approval_id}") from exc

    def list_open(self, *, shop_id: str | None = None) -> list[Approval]:
        with self._lock:
            return [
                approval
                for approval in self._items.values()
                if approval.is_open and (shop_id is None or approval.shop_id == shop_id)
            ]

    def find_open(self, shop_id: str, action_type: str, subject_key: str) -> Approval | None:
        for approval in self.list_open(shop_id=shop_id):
            if approval.action_type == action_type and approval.subject_key == subject_key:
                return approval
        return None

    def all(self) -> Iterable[Approval]:
        with self._lock:
            return tuple(self._items.values())

    # -- writes -----------------------------------------------------------
    def add(self, approval: Approval) -> Approval:
        with self._lock:
            if approval.id in self._items:
                raise ToolGateError("VERSION_CONFLICT", f"approval id already used: {approval.id}")
            existing = self.find_open(approval.shop_id, approval.action_type, approval.subject_key)
            if existing is not None:
                raise ToolGateError(
                    "VERSION_CONFLICT",
                    f"an open approval already exists for this subject: {existing.id}",
                )
            self._items[approval.id] = approval
            return approval

    def save(self, approval: Approval) -> Approval:
        with self._lock:
            current = self._items.get(approval.id)
            if current is None:
                raise KeyError(f"approval not found: {approval.id}")
            if approval.version != current.version + 1:
                raise ToolGateError(
                    "VERSION_CONFLICT",
                    f"expected version {current.version + 1}, got {approval.version}",
                )
            if approval.status in OPEN_STATUSES:
                other = self.find_open(
                    approval.shop_id, approval.action_type, approval.subject_key
                )
                if other is not None and other.id != approval.id:
                    raise ToolGateError(
                        "VERSION_CONFLICT", f"another open approval exists: {other.id}"
                    )
            self._items[approval.id] = approval
            return approval

    def try_begin_execution(self, approval_id: str, *, now) -> Approval:
        """CAS APPROVED -> EXECUTING; a second call must not succeed (INV-17)."""
        with self._lock:
            current = self._items.get(approval_id)
            if current is None:
                raise KeyError(f"approval not found: {approval_id}")
            if current.status is not ApprovalStatus.APPROVED:
                if current.status in (ApprovalStatus.DRAFT, ApprovalStatus.PENDING):
                    raise ToolGateError(
                        "NOT_APPROVED",
                        f"approval {approval_id} is {current.status.value}; a decision is still pending",
                    )
                raise ToolGateError(
                    "APPROVAL_ALREADY_CONSUMED",
                    f"approval {approval_id} is {current.status.value}, not APPROVED",
                )
            updated = current.transition(ApprovalStatus.EXECUTING, now=now)
            self._items[approval_id] = updated
            return updated


__all__ = ["ApprovalRepo", "InMemoryApprovalRepo"]
