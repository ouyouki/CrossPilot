"""INV-5: the "never grantable" list cannot reach a grant."""

from __future__ import annotations

import unittest
from decimal import Decimal

from crosspilot.core.clock import FixedClock
from crosspilot.core.errors import ToolGateError
from crosspilot.grants.engine import NEVER_GRANTABLE, GrantEngine
from crosspilot.registry.actions import REGISTRY, is_grantable

from .support import NOW


class Inv05NeverGrantable(unittest.TestCase):
    def test_only_consent_1_is_grantable(self):
        grantable = {name for name in REGISTRY if is_grantable(name)}
        self.assertEqual(grantable, {"ACT-SELECT"})

    def test_never_grantable_actions_are_refused(self):
        engine = GrantEngine(FixedClock(NOW))
        must_be_refused = set(NEVER_GRANTABLE) | {
            "ACT-SELECT-ALL",
            "ACT-SCORE",
            "ACT-COST-CALC",
        }
        for action in sorted(must_be_refused):
            with self.subTest(action=action), self.assertRaises(ToolGateError) as ctx:
                engine.require_grantable(action)
            self.assertEqual(ctx.exception.code, "NOT_GRANTABLE")

    def test_grant_create_cites_an_approval_and_a_reason(self):
        from crosspilot.grants.engine import Envelope

        engine = GrantEngine(FixedClock(NOW))
        envelope = Envelope(
            categories=frozenset({"home"}),
            price_min=1000,
            price_max=3000,
            min_margin=Decimal("0.28"),
            max_per_day=3,
        )
        with self.assertRaises(ToolGateError):
            engine.create(
                shop_id="shop-1",
                envelope=envelope,
                created_by="u-owner",
                created_from_approval_id="",
                max_uses=5,
                reason="batch of similar items",
            )
        with self.assertRaises(ToolGateError):
            engine.create(
                shop_id="shop-1",
                envelope=envelope,
                created_by="u-owner",
                created_from_approval_id="ap-1",
                max_uses=5,
                reason="   ",
            )


if __name__ == "__main__":
    unittest.main()
