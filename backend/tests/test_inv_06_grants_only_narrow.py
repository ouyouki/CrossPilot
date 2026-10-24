"""INV-6: a grant can only be narrowed; widening is refused, never applied."""

from __future__ import annotations

import unittest
from datetime import timedelta
from decimal import Decimal

from crosspilot.core.clock import FixedClock
from crosspilot.core.errors import ToolGateError
from crosspilot.grants.engine import Envelope, GrantEngine

from .support import NOW


def envelope(**overrides) -> Envelope:
    base = dict(
        categories=frozenset({"home"}),
        price_min=1000,
        price_max=3000,
        min_margin=Decimal("0.28"),
        max_per_day=3,
    )
    base.update(overrides)
    return Envelope(**base)


def make_grant(engine: GrantEngine):
    return engine.create(
        shop_id="shop-1",
        envelope=envelope(),
        created_by="u-owner",
        created_from_approval_id="ap-1",
        max_uses=10,
        reason="clearance category, all checks pass",
        now=NOW,
    )


class Inv06GrantsOnlyNarrow(unittest.TestCase):
    def setUp(self):
        self.clock = FixedClock(NOW)
        self.engine = GrantEngine(self.clock)

    def test_creation_delays_effect_and_caps_lifetime(self):
        grant = make_grant(self.engine)
        self.assertEqual(grant.effective_from, NOW + timedelta(hours=24))
        self.assertEqual(grant.expires_at, NOW + timedelta(days=30))

        with self.assertRaises(ToolGateError):
            self.engine.create(
                shop_id="shop-1",
                envelope=envelope(),
                created_by="u-owner",
                created_from_approval_id="ap-1",
                max_uses=3,
                reason="too long",
                now=NOW,
                ttl_days=31,
            )

    def test_narrowing_is_accepted(self):
        grant = make_grant(self.engine)
        narrowed = self.engine.narrow(
            grant.id,
            envelope=envelope(
                categories=frozenset({"home"}),
                price_min=1500,
                price_max=2500,
                min_margin=Decimal("0.30"),
                max_per_day=2,
                source_grade_min="A",
            ),
            max_uses=5,
            expires_at=NOW + timedelta(days=10),
        )
        self.assertEqual(narrowed.max_uses, 5)
        self.assertEqual(narrowed.envelope.max_per_day, 2)

    def test_widening_is_refused(self):
        grant = make_grant(self.engine)
        widenings = [
            {"envelope": envelope(categories=frozenset({"home", "beauty"}))},
            {"envelope": envelope(price_min=500)},
            {"envelope": envelope(price_max=9000)},
            {"envelope": envelope(min_margin=Decimal("0.20"))},
            {"envelope": envelope(max_per_day=5)},
            {"envelope": envelope(source_grade_min="C")},
            {"max_uses": 11},
            {"expires_at": NOW + timedelta(days=31)},
        ]
        for change in widenings:
            with self.subTest(change=change), self.assertRaises(ToolGateError) as ctx:
                self.engine.narrow(grant.id, **change)
            self.assertEqual(ctx.exception.code, "GRANT_WIDEN_FORBIDDEN")

        unchanged = self.engine.get(grant.id)
        self.assertEqual(unchanged.max_uses, 10)
        self.assertEqual(unchanged.envelope.max_per_day, 3)

    def test_revocation_is_immediate(self):
        grant = make_grant(self.engine)
        revoked = self.engine.revoke(grant.id, actor_id="u-owner", now=NOW)
        self.assertEqual(revoked.status.value, "REVOKED")
        self.assertFalse(revoked.is_active(NOW + timedelta(days=2)))


if __name__ == "__main__":
    unittest.main()
