"""INV-16: money is exact, payload hashing is canonical, floats never appear."""

from __future__ import annotations

import unittest
from decimal import Decimal

from crosspilot.core.money import (
    CanonicalisationError,
    canonical_json,
    jpy,
    margin_equal,
    payload_hash,
    sum_line_items,
)


class Inv16Money(unittest.TestCase):
    def test_float_is_refused_outright(self):
        with self.assertRaises(CanonicalisationError):
            canonical_json({"price": 1240.0})
        with self.assertRaises(CanonicalisationError):
            payload_hash({"price": 0.1})
        with self.assertRaises(CanonicalisationError):
            canonical_json({"price": Decimal("1240")})

    def test_canonical_form_is_key_order_independent(self):
        left = {"b": 2, "a": {"y": 1, "x": "日本語"}}
        right = {"a": {"x": "日本語", "y": 1}, "b": 2}
        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(payload_hash(left), payload_hash(right))
        self.assertEqual(canonical_json(left), '{"a":{"x":"日本語","y":1},"b":2}')

    def test_rounding_is_per_item_then_summed(self):
        # 0.5 + 0.5 rounds to 1 + 1 = 2, whereas rounding the sum gives 1.
        self.assertEqual(sum_line_items([Decimal("0.5"), Decimal("0.5")]), 2)
        self.assertEqual(jpy(Decimal("1.5")), 2)
        self.assertEqual(jpy(Decimal("1.4")), 1)

    def test_margin_comparison_is_four_places(self):
        self.assertTrue(margin_equal(Decimal("0.12344"), Decimal("0.12343")))
        self.assertFalse(margin_equal(Decimal("0.1234"), Decimal("0.1235")))

    def test_string_money_is_accepted_without_binary_float(self):
        self.assertEqual(jpy("1240"), 1240)
        self.assertEqual(jpy("1240.4"), 1240)


if __name__ == "__main__":
    unittest.main()
