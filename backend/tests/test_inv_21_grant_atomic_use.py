"""INV-21: grant usage is consumed atomically.

``used_count <= max_uses`` and the daily cap must hold under concurrency. The
in-memory engine uses a lock to stand in for ``UPDATE ... WHERE used_count <
max_uses RETURNING``; the PostgreSQL version will use that statement.
"""

from __future__ import annotations

import threading
import unittest
from datetime import timedelta
from decimal import Decimal

from crosspilot.core.clock import FixedClock
from crosspilot.core.errors import ToolGateError
from crosspilot.grants.engine import Envelope, GrantEngine

from .support import NOW


def _engine(*, max_uses: int, max_per_day: int) -> tuple[GrantEngine, str]:
    engine = GrantEngine(FixedClock(NOW))
    grant = engine.create(
        shop_id="shop-1",
        envelope=Envelope(
            categories=frozenset({"home"}),
            price_min=1000,
            price_max=3000,
            min_margin=Decimal("0.25"),
            max_per_day=max_per_day,
        ),
        created_by="u-owner",
        created_from_approval_id="ap-1",
        max_uses=max_uses,
        reason="concurrent consumption test",
        now=NOW,
    )
    return engine, grant.id


def _race(engine: GrantEngine, grant_id: str, threads: int, *, at) -> int:
    successes = 0
    lock = threading.Lock()

    def worker(index: int) -> None:
        nonlocal successes
        try:
            engine.consume(grant_id, approval_id=f"ap-{index}", now=at)
        except ToolGateError:
            return
        with lock:
            successes += 1

    pool = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
    for thread in pool:
        thread.start()
    for thread in pool:
        thread.join()
    return successes


class Inv21GrantAtomicUse(unittest.TestCase):
    def test_used_count_never_exceeds_max_uses(self):
        engine, grant_id = _engine(max_uses=5, max_per_day=100)
        at = NOW + timedelta(days=2)

        successes = _race(engine, grant_id, threads=24, at=at)

        self.assertEqual(successes, 5)
        self.assertEqual(engine.get(grant_id).used_count, 5)

    def test_daily_cap_is_enforced(self):
        engine, grant_id = _engine(max_uses=10, max_per_day=2)
        at = NOW + timedelta(days=2)

        successes = _race(engine, grant_id, threads=12, at=at)

        self.assertEqual(successes, 2)
        self.assertEqual(engine.get(grant_id).used_count, 2)

    def test_grant_does_not_work_before_it_takes_effect(self):
        engine, grant_id = _engine(max_uses=5, max_per_day=5)
        with self.assertRaises(ToolGateError):
            engine.consume(grant_id, approval_id="ap-early", now=NOW + timedelta(hours=1))

    def test_expiry_blocks_consumption(self):
        engine, grant_id = _engine(max_uses=5, max_per_day=5)
        with self.assertRaises(ToolGateError):
            engine.consume(grant_id, approval_id="ap-late", now=NOW + timedelta(days=31))


if __name__ == "__main__":
    unittest.main()
