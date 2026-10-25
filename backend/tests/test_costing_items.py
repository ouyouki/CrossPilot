"""到岸成本与利润:金额、取整与来源(TC-4-01/05/06/07/08/12/14/16)。"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from crosspilot.costing import (
    Assumptions,
    CostInput,
    FxRate,
    ItemStatus,
    ListingFacts,
    RateValue,
    ResultStatus,
    Severity,
    TaxRegime,
    compute,
)


def card(**overrides: RateValue) -> dict[str, RateValue]:
    base: dict[str, RateValue] = {
        "c1_goods": RateValue(Decimal("100"), unit="CNY", source="供貨表", status=ItemStatus.CONFIRMED),
        "c2_domestic_ship": RateValue(Decimal("10"), unit="CNY", source="供貨表"),
        "c3_intl_ship": RateValue(800, source="貨代報價"),
        "c4_customs_duty_rate": RateValue(Decimal("0.10"), unit="rate", source="税関"),
        "c5_consumption_tax_rate": RateValue(Decimal("0.10"), unit="rate", source="国税庁"),
        "c6_customs_fee": RateValue(300, source="通関業者"),
        "c7_packaging": RateValue(100, source="包材"),
        "c8_commission_rate": RateValue(Decimal("0.10"), unit="rate", source="平台費率"),
        "c9_payment_fee_rate": RateValue(Decimal("0.02"), unit="rate", source="平台費率"),
        "c14_settlement_rate": RateValue(Decimal("0.01"), unit="rate", source="銀行"),
        "c15_loss_rate": RateValue(Decimal("0.01"), unit="rate", source="実績"),
        "c11_affiliate_rate": RateValue(Decimal("0"), unit="rate", source="未開通"),
        "c12_ad_per_unit": RateValue(0, source="未投放"),
        "c13_promo_per_unit": RateValue(0, source="无活動"),
    }
    base.update(overrides)
    return base


def make_input(**overrides) -> CostInput:
    params = dict(
        rate_card=card(),
        fx=FxRate(rate=Decimal("20"), ref_date=date(2026, 10, 24), source_id="fx-1"),
        tax=TaxRegime.DE_MINIMIS_EXEMPT,
        listing=ListingFacts(price_jpy=6000, buyer_shipping_fee_jpy=0, weight_g=500, sample_cost_jpy=0, expected_sales=30),
        assumptions=Assumptions(
            return_rate=Decimal("0.2"),
            refund_commission_return=Decimal("0"),
            unsellable_ratio=Decimal("0.5"),
            return_shipping_jpy=0,
            order_units=1,
        ),
    )
    params.update(overrides)
    return CostInput(**params)


def item(result, key):
    return next(i for i in result.items if i.key == key)


class CostingItems(unittest.TestCase):
    def test_TC_4_01_landed_cost_from_cny_and_table(self):
        # TC-4-01: c1/c2 由 CNY×汇率,c3 来自运费;三项都在结果里
        result = compute(make_input())
        self.assertIs(result.status, ResultStatus.COMPUTED)
        self.assertEqual(item(result, "c1_goods").value_jpy, 2000)
        self.assertEqual(item(result, "c2_domestic_ship").value_jpy, 200)
        self.assertEqual(item(result, "c3_intl_ship").value_jpy, 800)

    def test_TC_4_05_commission_and_return_loss_are_not_in_landed_cost(self):
        # TC-4-05: 佣金与退货损耗单列,不并入到岸成本
        result = compute(make_input())
        landed = sum(
            item(result, k).value_jpy
            for k in ("c1_goods", "c2_domestic_ship", "c3_intl_ship", "c4_customs_duty",
                      "c5_import_consumption_tax", "c6_customs_fee", "c7_packaging")
        )
        self.assertEqual(landed, 3400)
        self.assertEqual(item(result, "c8_commission").value_jpy, 600)
        self.assertEqual(item(result, "c10_return_loss").value_jpy, 1200)

    def test_TC_4_06_zero_items_are_confirmed_not_missing(self):
        # TC-4-06: 显式填 0 的三项是 CONFIRMED,不是 MISSING
        result = compute(make_input())
        for key in ("c11_affiliate", "c12_ad", "c13_promo"):
            with self.subTest(key=key):
                self.assertEqual(item(result, key).value_jpy, 0)
                self.assertIs(item(result, key).status, ItemStatus.CONFIRMED)

    def test_TC_4_07_rounding_is_per_item_then_summed(self):
        # TC-4-07: 0.5 + 0.5 逐项取整得 2(求和后取整会得 1)
        half = RateValue(Decimal("0.5"), unit="CNY")
        result = compute(
            make_input(
                rate_card=card(c1_goods=half, c2_domestic_ship=half),
                fx=FxRate(rate=Decimal("1"), ref_date=date(2026, 10, 24), source_id="fx-1"),
            )
        )
        self.assertEqual(item(result, "c1_goods").value_jpy, 1)
        self.assertEqual(item(result, "c2_domestic_ship").value_jpy, 1)

    def test_TC_4_08_margin_compares_at_four_places(self):
        # TC-4-08: 同一输入两次计算,margin 在 4 位小数上一致
        first = compute(make_input())
        second = compute(make_input())
        self.assertEqual(first.margin, second.margin)
        self.assertEqual(first.margin, Decimal("0.0977"))

    def test_TC_4_12_every_item_carries_source_and_freshness(self):
        # TC-4-12: 每项都能说出从哪来
        result = compute(make_input())
        for entry in result.items:
            with self.subTest(key=entry.key):
                self.assertIsInstance(entry.source, str)
                self.assertIn("status", dir(entry))

    def test_TC_4_14_fx_snapshot_id_is_returned(self):
        # TC-4-14: 结果引用汇率快照
        result = compute(make_input())
        self.assertEqual(result.fx_rate_id, "fx-1")

    def test_TC_4_16_zero_revenue_does_not_divide_by_zero(self):
        # TC-4-16: 售价与运费都为 0 时 margin 为 None
        result = compute(make_input(listing=ListingFacts(price_jpy=0, buyer_shipping_fee_jpy=0)))
        self.assertEqual(result.revenue, 0)
        self.assertIsNone(result.margin)


if __name__ == "__main__":
    unittest.main()
