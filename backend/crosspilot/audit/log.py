"""Append-only audit log with a hash chain (04 §12, INV-11).

The log has no update or delete method by construction, and every refusal is
written too — a refused call is one of the more interesting rows in the table.
The chain is ``hash = sha256(prev_hash ‖ canonical(row))``; :meth:`verify`
recomputes the whole chain, so touching any earlier row breaks every later hash.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping

from ..core.money import canonical_json, sha256_hex

GENESIS = "0" * 64


class AuditDecision(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    HELD = "HELD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    seq: int
    ts: datetime
    actor_type: str
    actor_id: str
    action: str
    target: str
    decision: AuditDecision
    ruleset_version: str
    details: Mapping[str, Any]
    prev_hash: str
    hash: str


@dataclass(frozen=True, slots=True)
class VerifyResult:
    ok: bool
    broken_at: int | None = None
    reason: str = ""


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_jsonable(v) for v in value]
        return sorted(items, key=repr) if isinstance(value, (set, frozenset)) else items
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


class AuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._lock = threading.RLock()

    # -- reads -------------------------------------------------------------
    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def entries(self) -> tuple[AuditEntry, ...]:
        with self._lock:
            return tuple(self._entries)

    @property
    def last_seq(self) -> int:
        with self._lock:
            return self._entries[-1].seq if self._entries else 0

    def checkpoint(self) -> dict[str, Any]:
        with self._lock:
            if not self._entries:
                return {"last_seq": 0, "last_hash": GENESIS}
            head = self._entries[-1]
            return {"last_seq": head.seq, "last_hash": head.hash}

    # -- write (the only write operation) -----------------------------------
    def append(
        self,
        *,
        ts: datetime,
        actor_type: str,
        actor_id: str,
        action: str,
        target: str,
        decision: AuditDecision,
        ruleset_version: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> AuditEntry:
        with self._lock:
            prev_hash = self._entries[-1].hash if self._entries else GENESIS
            seq = (self._entries[-1].seq + 1) if self._entries else 1
            row = {
                "seq": seq,
                "ts": ts.isoformat(),
                "actor_type": actor_type,
                "actor_id": actor_id,
                "action": action,
                "target": target,
                "decision": decision.value,
                "ruleset_version": ruleset_version,
                "details": _jsonable(details or {}),
                "prev_hash": prev_hash,
            }
            digest = sha256_hex(prev_hash + canonical_json(row))
            entry = AuditEntry(
                seq=seq,
                ts=ts,
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                target=target,
                decision=decision,
                ruleset_version=ruleset_version,
                details=row["details"],
                prev_hash=prev_hash,
                hash=digest,
            )
            self._entries.append(entry)
            return entry

    # -- integrity ----------------------------------------------------------
    def verify(self) -> VerifyResult:
        with self._lock:
            prev = GENESIS
            for index, entry in enumerate(self._entries):
                if entry.prev_hash != prev:
                    return VerifyResult(False, entry.seq, "prev_hash does not match the chain")
                row = {
                    "seq": entry.seq,
                    "ts": entry.ts.isoformat(),
                    "actor_type": entry.actor_type,
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "target": entry.target,
                    "decision": entry.decision.value,
                    "ruleset_version": entry.ruleset_version,
                    "details": _jsonable(entry.details),
                    "prev_hash": entry.prev_hash,
                }
                expected = sha256_hex(prev + canonical_json(row))
                if entry.hash != expected:
                    return VerifyResult(False, entry.seq, "hash does not match the row")
                prev = entry.hash
            return VerifyResult(True)

    def for_subject(self, target: str) -> tuple[AuditEntry, ...]:
        with self._lock:
            return tuple(entry for entry in self._entries if entry.target == target)


__all__ = ["AuditDecision", "AuditEntry", "AuditLog", "GENESIS", "VerifyResult"]
