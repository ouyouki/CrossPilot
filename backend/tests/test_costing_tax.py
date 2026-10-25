"""税口径:六个 tax_regime(TC-4-02/03/04/11)。"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from crosspilot.costing import (
    Assumptions,
    CostInput,
    FxRate,
    ListingFacts,
    RateValue,
    ResultStatus,
    TaxRegime,
    compute,
)


def base_card() -> dict[str, RateValue]:
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


def compute_with(tax: TaxRegime):
    return compute(
        CostInput(
            rate_card=base_card(),
            fx=FxRate(rate=Decimal("20"), ref_date=date(2026, 10, 24), source_id="fx-1"),
            tax=tax,
            listing=ListingFacts(price_jpy=6000),
            assumptions=Assumptions(return_rate=Decimal("0"), order_units=1),
        )
    )


def value(result, key: str) -> int:
    return next(i.value_jpy for i in result.items if i.key == key)


class CostingTax(unittest.TestCase):
    def test_TC_4_02_de_minimis_has_no_duty_or_import_tax(self):
        # TC-4-02: 少額輸入免税 → c4/c5 为 0
        result = compute_with(TaxRegime.DE_MINIMIS_EXEMPT)
        self.assertEqual(value(result, "c4_customs_duty"), 0)
        self.assertEqual(value(result, "c5_import_consumption_tax"), 0)

    def test_TC_4_03_seller_is_ior_pays_duty_and_consumption_tax(self):
        # TC-4-03: 卖家是输入者 → 关税 10%×(c1+c3),输入消费税 10%×(课税价格+关税)
        result = compute_with(TaxRegime.SELLER_IOR_DDP)
        self.assertEqual(value(result, "c4_customs_duty"), 280)
        self.assertEqual(value(result, "c5_import_consumption_tax"), 308)

    def test_TC_4_04_unknown_tax_regime_has_no_profit(self):
        # TC-4-04: tax_regime=UNKNOWN → UNKNOWN,不给利润
        result = compute_with(TaxRegime.UNKNOWN)
        self.assertIs(result.status, ResultStatus.UNKNOWN)
        self.assertIn("tax_regime", result.missing)
        self.assertIsNone(result.profit)

    def test_TC_4_11_all_six_regimes_are_defined(self):
        # TC-4-11: 六个值都有确定行为;ASSUMED_WORST 标 assumed 且不被当成确认值
        expectations = {
            TaxRegime.DE_MINIMIS_EXEMPT: (0, 0, 6000, False),
            TaxRegime.SELLER_IOR_DDP: (280, 308, 5455, False),
            TaxRegime.SELLER_LIABLE_LOW_VALUE: (0, 0, 5455, False),
            TaxRegime.PLATFORM_COLLECTS: (280, 0, 6000, False),
            TaxRegime.ASSUMED_WORST: (280, 308, 5455, True),
        }
        for regime, (duty, tax, revenue, assumed) in expectations.items():
            with self.subTest(regime=regime):
                result = compute_with(regime)
                self.assertIs(result.status, ResultStatus.COMPUTED)
                self.assertEqual(value(result, "c4_customs_duty"), duty)
                self.assertEqual(value(result, "c5_import_consumption_tax"), tax)
                self.assertEqual(result.revenue, revenue)
                self.assertIs(result.assumed, assumed)

        self.assertIs(compute_with(TaxRegime.UNKNOWN).status, ResultStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
