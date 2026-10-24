"""Facts handed to the Gatekeeper.

A fact is either known or not. "Not known" covers three cases that the design
treats identically (they all stop the action, 01 §6 step 4):

* the key is absent,
* the value is the ``UNKNOWN`` sentinel (what the UI shows when data is missing),
* the value is ``None`` (a field that exists but was never filled).

Treating ``None`` as unknown is the stricter reading, and 00 §2 says to take the
stricter one when two readings disagree.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any


class _Unknown:
    """Sentinel for a missing external fact (displayed as UNKNOWN)."""

    _instance: "_Unknown | None" = None

    def __new__(cls) -> "_Unknown":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "UNKNOWN"

    def __bool__(self) -> bool:
        return False


UNKNOWN = _Unknown()


class Facts(Mapping[str, Any]):
    """Immutable fact bag with an explicit notion of "known"."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any] | None = None, /, **kwargs: Any) -> None:
        merged: dict[str, Any] = dict(data or {})
        merged.update(kwargs)
        self._data = merged

    # -- Mapping protocol -------------------------------------------------
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Facts({self._data!r})"

    # -- Domain helpers ---------------------------------------------------
    def is_known(self, name: str) -> bool:
        if name not in self._data:
            return False
        value = self._data[name]
        return value is not UNKNOWN and value is not None

    def known(self) -> frozenset[str]:
        return frozenset(name for name in self._data if self.is_known(name))

    def with_values(self, **changes: Any) -> "Facts":
        merged = dict(self._data)
        merged.update(changes)
        return Facts(merged)

    def without(self, *names: str) -> "Facts":
        merged = {k: v for k, v in self._data.items() if k not in names}
        return Facts(merged)

    def get_known(self, name: str, default: Any = UNKNOWN) -> Any:
        return self._data[name] if self.is_known(name) else default
