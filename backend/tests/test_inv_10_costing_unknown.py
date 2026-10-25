"""INV-10:任一 BLOCKING 项缺失 → 利润 UNKNOWN,不补默认值。

TC-4-09 / TC-4-10 / TC-4-13 / TC-4-15。
这条不变量是红线级的:利润显示成数字但实际算不出来,人就会按假数签字。
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from crosspilot.core.money import CanonicalisationError
from crosspilot.costing import (
    REQUIRED_CARD_KEYS,
    Assumptions,
    CostInput,
    FxRate,
    ItemStatus,
    ListingFacts,
    RateValue,
    ResultStatus,
    TaxRegime,
    compute,
)


def full_card() -> dict[str, RateValue]:
    return {
        "c1_goods": RateValue(Decimal("100"), unit="CNY"),
        "c2_domestic_ship": RateValue(Decimal("10"), unit="CNY"),
        "c3_intl_ship": RateValue(800),
        "c4_customs_duty_rate": RateValue(Decimal("0.10"), unit="rate"),
        "c5_consumption_tax_rate": RateValue(Decimal("0.10"), unit="rate"),
        "c6_customs_fee": RateValue(300),
        "c7_packaging": RateValue(100),
        "c8_commission_rate": RateValue(Decimal("0.10"), unit="rate"),
        "c9_payment_fee_rate": RateValue(Decimal("0.02"), unit="rate"),
        "c14_settlement_rate": RateValue(Decimal("0.01"), unit="rate"),
        "c15_loss_rate": RateValue(Decimal("0.01"), unit="rate"),
    }


def build(card: dict[str, RateValue]) -> CostInput:
    return CostInput(
        rate_card=card,
        fx=FxRate(rate=Decimal("20"), ref_date=date(2026, 10, 24), source_id="fx-1"),
        tax=TaxRegime.DE_MINIMIS_EXEMPT,
        listing=ListingFacts(price_jpy=6000),
        assumptions=Assumptions(return_rate=Decimal("0")),
    )


class Inv10MissingBlocking(unittest.TestCase):
    def test_TC_4_09_missing_intl_ship_is_unknown(self):
        # TC-4-09: 缺国际运费 → UNKNOWN,missing 指出这一项
        card = full_card()
        card["c3_intl_ship"] = RateValue(status=ItemStatus.MISSING)
        result = compute(build(card))
        self.assertIs(result.status, ResultStatus.UNKNOWN)
        self.assertIn("c3_intl_ship", result.missing)
        self.assertIsNone(result.profit)

    def test_TC_4_10_deleting_any_blocking_item_never_yields_profit(self):
        # TC-4-10: 逐个删掉 BLOCKING 项,永远不是 COMPUTED
        for key in (*REQUIRED_CARD_KEYS, "c3_intl_ship"):
            with self.subTest(key=key):
                card = full_card()
                del card[key]
                result = compute(build(card))
                self.assertIs(result.status, ResultStatus.UNKNOWN, key)
                self.assertIsNone(result.profit, key)
                self.assertIn(key, result.missing)

    def test_TC_4_15_empty_card_lists_every_blocking_item(self):
        # TC-4-15: 空费率卡 → missing 覆盖全部 BLOCKING 项
        result = compute(build({}))
        self.assertIs(result.status, ResultStatus.UNKNOWN)
        for key in (*REQUIRED_CARD_KEYS, "c3_intl_ship"):
            self.assertIn(key, result.missing)

    def test_TC_4_13_float_money_is_rejected(self):
        # TC-4-13: 金额不能是 float
        with self.assertRaises(CanonicalisationError):
            RateValue(1.5)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
