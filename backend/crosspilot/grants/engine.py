"""Grant (authorization list) engine — RL-2 in code (04 §7).

What this module is allowed to do is as important as what it can:

* it can **narrow** a grant, never widen one (widening is a new grant, 24 h
  later, and goes through ACT-CREATE-GRANT);
* it consumes uses atomically, so ``used_count`` can never exceed ``max_uses``
  nor a day's ``max_per_day`` even under concurrency (INV-21);
* it is ordinary code called from a deterministic path — the Pilot agent has no
  tool that could reach it (05 §3.1).

The one action it can ever authorize is ACT-SELECT (consent 1); consent 2,
budget release and every other red-light action stay permanently un-grantable.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Mapping

from ..core.clock import JST
from ..core.errors import ToolGateError
from ..core.money import dec, q4
from ..registry.actions import is_grantable

#: 04 §7.2 / INV-5: the permanent exclusion list, restated as data.
NEVER_GRANTABLE: frozenset[str] = frozenset(
    {
        "ACT-APPROVE-ASSETS",
        "ACT-LIST-CREATE",
        "ACT-RELEASE-COST-GATE",
        "ACT-ACK-DISPATCH-RISK",
        "ACT-ACCEPT-MISMATCH",
        "ACT-LOOSEN-RULE",
        "ACT-CREATE-GRANT",
        "ACT-ADOPT-WEIGHT-SUGGESTION",
    }
)

GRANT_ACTION = "ACT-SELECT"
GRANT_MAX_DAYS = 30
GRANT_DELAY = timedelta(hours=24)

_GRADE_ORDER = {"A": 3, "B": 2, "C": 1}


class GrantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


@dataclass(frozen=True, slots=True)
class CandidateFacts:
    """The subset of candidate facts a grant envelope is allowed to look at."""

    category: str
    price_jpy: int
    margin: Decimal
    profit_computable: bool
    g0_pass: bool
    degrading: bool = False
    source_grade: str = "B"


@dataclass(frozen=True, slots=True)
class Envelope:
    categories: frozenset[str]
    price_min: int
    price_max: int
    min_margin: Decimal
    max_per_day: int
    source_grade_min: str = "B"
    require_profit_computable: bool = True
    require_g0_pass: bool = True
    require_no_degrading: bool = True

    def __post_init__(self) -> None:
        if self.price_min > self.price_max:
            raise ValueError("price_min must not exceed price_max")
        if self.max_per_day < 1:
            raise ValueError("max_per_day must be >= 1")
        if self.source_grade_min not in _GRADE_ORDER:
            raise ValueError(f"unknown source grade: {self.source_grade_min}")

    def covers(self, candidate: CandidateFacts) -> bool:
        if candidate.category not in self.categories:
            return False
        if not (self.price_min <= candidate.price_jpy <= self.price_max):
            return False
        if q4(candidate.margin) < q4(self.min_margin):
            return False
        if self.require_profit_computable and not candidate.profit_computable:
            return False
        if self.require_g0_pass and not candidate.g0_pass:
            return False
        if self.require_no_degrading and candidate.degrading:
            return False
        return _GRADE_ORDER[candidate.source_grade] >= _GRADE_ORDER[self.source_grade_min]


@dataclass(frozen=True, slots=True)
class GrantUse:
    grant_id: str
    approval_id: str
    used_at: datetime
    within_envelope: bool
    sampled: bool
    sample_result: str | None = None


@dataclass(frozen=True, slots=True)
class Grant:
    id: str
    shop_id: str
    action_type: str
    envelope: Envelope
    created_by: str
    created_from_approval_id: str
    created_at: datetime
    effective_from: datetime
    expires_at: datetime
    max_uses: int
    reason: str = ""
    used_count: int = 0
    status: GrantStatus = GrantStatus.ACTIVE
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    sampling_rate: Decimal = Decimal("0.2")
    #: Daily counters keyed by Asia/Tokyo date (04 §7.2 rule 2).
    daily_uses: Mapping[date, int] = field(default_factory=dict)

    def uses_on(self, day: date) -> int:
        return self.daily_uses.get(day, 0)

    def is_active(self, now: datetime) -> bool:
        return (
            self.status is GrantStatus.ACTIVE
            and self.effective_from <= now < self.expires_at
        )


class GrantEngine:
    """In-memory grant store with the DB's atomic-update semantics."""

    def __init__(self, clock) -> None:
        self.clock = clock
        self._grants: dict[str, Grant] = {}
        self._uses: list[GrantUse] = []
        self._lock = threading.RLock()

    # -- reads ------------------------------------------------------------
    def get(self, grant_id: str) -> Grant:
        try:
            return self._grants[grant_id]
        except KeyError as exc:
            raise ToolGateError("NOT_GRANTABLE", f"grant not found: {grant_id}") from exc

    def uses(self) -> tuple[GrantUse, ...]:
        with self._lock:
            return tuple(self._uses)

    # -- creation ----------------------------------------------------------
    def create(
        self,
        *,
        shop_id: str,
        envelope: Envelope,
        created_by: str,
        created_from_approval_id: str,
        max_uses: int,
        reason: str,
        now: datetime | None = None,
        ttl_days: int = GRANT_MAX_DAYS,
        grant_id: str | None = None,
        sampling_rate: Decimal = Decimal("0.2"),
    ) -> Grant:
        now = now or self.clock.now()
        if not is_grantable(GRANT_ACTION):
            raise ToolGateError("NOT_GRANTABLE", "ACT-SELECT is not grantable in this build")
        if not created_from_approval_id:
            raise ToolGateError("NOT_GRANTABLE", "a grant must cite the approval it came from")
        if max_uses < 1:
            raise ToolGateError("NOT_GRANTABLE", "max_uses must be >= 1")
        if not reason.strip():
            raise ToolGateError(
                "NOT_GRANTABLE",
                "a grant needs a written reason (04 §7.2 rule 4)",
            )
        if ttl_days < 1 or ttl_days > GRANT_MAX_DAYS:
            raise ToolGateError(
                "NOT_GRANTABLE", f"grant lifetime must be 1..{GRANT_MAX_DAYS} days"
            )
        grant = Grant(
            id=grant_id or f"g-{uuid.uuid4().hex[:12]}",
            shop_id=shop_id,
            action_type=GRANT_ACTION,
            envelope=envelope,
            created_by=created_by,
            created_from_approval_id=created_from_approval_id,
            created_at=now,
            effective_from=now + GRANT_DELAY,
            expires_at=now + timedelta(days=ttl_days),
            max_uses=max_uses,
            reason=reason,
            sampling_rate=sampling_rate,
        )
        with self._lock:
            if grant.id in self._grants:
                raise ToolGateError("NOT_GRANTABLE", f"grant id already used: {grant.id}")
            self._grants[grant.id] = grant
        return grant

    def require_grantable(self, action_type: str) -> None:
        if action_type in NEVER_GRANTABLE or not is_grantable(action_type):
            raise ToolGateError(
                "NOT_GRANTABLE", f"{action_type} can never be added to the authorization list"
            )

    # -- narrowing (INV-6) --------------------------------------------------
    def narrow(
        self,
        grant_id: str,
        *,
        envelope: Envelope | None = None,
        max_uses: int | None = None,
        expires_at: datetime | None = None,
        now: datetime | None = None,
    ) -> Grant:
        """Apply a change that only ever narrows. Anything else is refused."""
        with self._lock:
            grant = self.get(grant_id)
            if grant.status is not GrantStatus.ACTIVE:
                raise ToolGateError("NOT_GRANTABLE", f"grant is {grant.status.value}")
            if envelope is not None:
                _assert_narrower(grant.envelope, envelope)
            if max_uses is not None and max_uses > grant.max_uses:
                raise ToolGateError(
                    "GRANT_WIDEN_FORBIDDEN",
                    f"max_uses can only decrease ({grant.max_uses} -> {max_uses} is a widening)",
                )
            if expires_at is not None and expires_at > grant.expires_at:
                raise ToolGateError(
                    "GRANT_WIDEN_FORBIDDEN",
                    "expires_at can only move earlier",
                )
            updated = replace(
                grant,
                envelope=envelope if envelope is not None else grant.envelope,
                max_uses=min(grant.max_uses, max_uses) if max_uses is not None else grant.max_uses,
                expires_at=expires_at if expires_at is not None else grant.expires_at,
            )
            self._grants[grant_id] = updated
            return updated

    # -- state changes -------------------------------------------------------
    def revoke(self, grant_id: str, *, actor_id: str, now: datetime | None = None) -> Grant:
        now = now or self.clock.now()
        with self._lock:
            grant = self.get(grant_id)
            if grant.status is GrantStatus.REVOKED:
                return grant
            updated = replace(
                grant, status=GrantStatus.REVOKED, revoked_by=actor_id, revoked_at=now
            )
            self._grants[grant_id] = updated
            return updated

    def suspend(self, grant_id: str, *, reason: str, now: datetime) -> Grant:
        with self._lock:
            grant = self.get(grant_id)
            updated = replace(grant, status=GrantStatus.SUSPENDED, revoked_by=reason)
            self._grants[grant_id] = updated
            return updated

    def restore_baseline(self, grant_id: str, *, now: datetime) -> Grant:
        """Restoring a suspended grant is immediate and audited (04 §8)."""
        with self._lock:
            grant = self.get(grant_id)
            updated = replace(grant, status=GrantStatus.ACTIVE, revoked_by=None, revoked_at=None)
            self._grants[grant_id] = updated
            return updated

    # -- matching and consumption -------------------------------------------
    def can_delegate(
        self, grant_id: str, candidate: CandidateFacts, *, now: datetime | None = None
    ) -> bool:
        now = now or self.clock.now()
        with self._lock:
            grant = self.get(grant_id)
            if not grant.is_active(now):
                return False
            if grant.used_count >= grant.max_uses:
                return False
            if grant.uses_on(_jst_date(now)) >= grant.envelope.max_per_day:
                return False
            return grant.envelope.covers(candidate)

    def consume(
        self,
        grant_id: str,
        *,
        approval_id: str,
        now: datetime | None = None,
        within_envelope: bool = True,
    ) -> Grant:
        """Atomically take one use.

        Mirrors the SQL in 06 §7: the UPDATE only matches while the grant is
        ACTIVE, inside its window and below both caps. Here the lock plays the
        part of the row lock.
        """
        now = now or self.clock.now()
        with self._lock:
            grant = self.get(grant_id)
            if not grant.is_active(now):
                raise ToolGateError("NOT_APPROVED", f"grant {grant_id} is not active")
            if grant.used_count >= grant.max_uses:
                raise ToolGateError("NOT_APPROVED", f"grant {grant_id} is used up")
            day = _jst_date(now)
            used_today = grant.uses_on(day)
            if used_today >= grant.envelope.max_per_day:
                raise ToolGateError(
                    "NOT_APPROVED",
                    f"grant {grant_id} already reached max_per_day={grant.envelope.max_per_day}",
                )
            daily = dict(grant.daily_uses)
            daily[day] = used_today + 1
            updated = replace(grant, used_count=grant.used_count + 1, daily_uses=daily)
            self._grants[grant_id] = updated
            sampled = _sample(updated)
            self._uses.append(
                GrantUse(
                    grant_id=grant_id,
                    approval_id=approval_id,
                    used_at=now,
                    within_envelope=within_envelope,
                    sampled=sampled,
                )
            )
            return updated

    def record_sample_result(
        self, approval_id: str, *, ok: bool, now: datetime | None = None
    ) -> Grant | None:
        """One bad sampled delegation suspends the grant (04 §7.2 rule 6)."""
        now = now or self.clock.now()
        with self._lock:
            for index, use in enumerate(self._uses):
                if use.approval_id != approval_id:
                    continue
                self._uses[index] = replace(use, sample_result="OK" if ok else "REJECT")
                if not ok:
                    return self.suspend(use.grant_id, reason="sampling found a bad delegation", now=now)
            return None


def _assert_narrower(old: Envelope, new: Envelope) -> None:
    if not new.categories <= old.categories:
        raise ToolGateError(
            "GRANT_WIDEN_FORBIDDEN", "categories must be a subset of the existing envelope"
        )
    if new.price_min < old.price_min or new.price_max > old.price_max:
        raise ToolGateError("GRANT_WIDEN_FORBIDDEN", "price band can only shrink")
    if q4(new.min_margin) < q4(old.min_margin):
        raise ToolGateError("GRANT_WIDEN_FORBIDDEN", "min_margin can only increase")
    if new.max_per_day > old.max_per_day:
        raise ToolGateError("GRANT_WIDEN_FORBIDDEN", "max_per_day can only decrease")
    if _GRADE_ORDER[new.source_grade_min] < _GRADE_ORDER[old.source_grade_min]:
        raise ToolGateError("GRANT_WIDEN_FORBIDDEN", "source_grade_min can only get stricter")
    for flag in ("require_profit_computable", "require_g0_pass", "require_no_degrading"):
        if getattr(old, flag) and not getattr(new, flag):
            raise ToolGateError(
                "GRANT_WIDEN_FORBIDDEN", f"{flag} can only go from False to True"
            )


def _jst_date(moment: datetime) -> date:
    return moment.astimezone(JST).date()


def _sample(grant: Grant) -> bool:
    # Deterministic sampling: every Nth use is audited, no RNG in the decision
    # path (RL-3). rate 0.2 -> every 5th use.
    rate = dec(grant.sampling_rate)
    if rate <= 0:
        return False
    step = max(1, int(dec(1) / rate))
    return grant.used_count % step == 0


__all__ = [
    "CandidateFacts",
    "Envelope",
    "GRANT_ACTION",
    "GRANT_DELAY",
    "GRANT_MAX_DAYS",
    "Grant",
    "GrantEngine",
    "GrantStatus",
    "GrantUse",
    "NEVER_GRANTABLE",
]
