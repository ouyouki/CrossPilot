"""Injectable clock.

INV-2 is tested by fast-forwarding a fake clock one year and asserting that a
PENDING approval is still PENDING, so nothing in the engine may read wall time
directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

JST = timezone(timedelta(hours=9), name="Asia/Tokyo")


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)


class FixedClock:
    """A clock that only moves when told to."""

    __slots__ = ("_now",)

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 10, 24, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now = self._now + delta

    def set(self, moment: datetime) -> None:
        self._now = moment
