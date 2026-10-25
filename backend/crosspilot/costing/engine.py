"""到岸成本与利润的唯一实现(03 §3.1)。纯函数:无 I/O、无时钟、无 LLM。

INV-10 的落点在这里:任一 BLOCKING 项缺失时返回 ``status=UNKNOWN``,不产出任何
金额,也不补默认值——"缺三项,补哪三项"比"一个看起来合理的数"有用。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Mapping

from ..core.money import CanonicalisationError, dec, jpy, q4
from .types import (
    Assumptions,
    CostInput,
    CostItem,
    CostResult,
    ItemStatus,
    ListingFacts,
    RateValue,
    ResultStatus,
    ReturnMode,
    Severity,
    TaxRegime,
)

# 结果里的 16 个成本项(02-设计 §3)。
ITEM_C1 = "c1_goods"
ITEM_C2 = "c2_domestic_ship"
ITEM_C3 = "c3_intl_ship"
ITEM_C4 = "c4_customs_duty"
ITEM_C5 = "c5_import_consumption_tax"
ITEM_C6 = "c6_customs_fee"
ITEM_C7 = "c7_packaging"
ITEM_C8 = "c8_commission"
ITEM_C9 = "c9_payment_fee"
ITEM_C10 = "c10_return_loss"
ITEM_C11 = "c11_affiliate"
ITEM_C12 = "c12_ad"
ITEM_C13 = "c13_promo"
ITEM_C14 = "c14_settlement_fx"
ITEM_C15 = "c15_lost_damage"
ITEM_C16 = "c16_sample_amortization"

# 费率卡里必须存在的键(不含 c3:c3 可以来自运费表)。
REQUIRED_CARD_KEYS: tuple[str, ...] = (
    "c1_goods",
    "c2_domestic_ship",
    "c4_customs_duty_rate",
    "c5_consumption_tax_rate",
    "c6_customs_fee",
    "c7_packaging",
    "c8_commission_rate",
    "c9_payment_fee_rate",
    "c14_settlement_rate",
    "c15_loss_rate",
)

# 只有低价值货物口径才适用 1 万日元门槛(U-3b 未核实,仅此一处)。
_LOW_VALUE_THRESHOLD_JPY = 10_000

# tax_regime → (是否计关税, 是否计输入消费税, 卖家是否负担销项税)
_TAX_PROFILE: Mapping[TaxRegime, tuple[bool, bool, bool]] = {
    TaxRegime.DE_MINIMIS_EXEMPT: (False, False, False),
    TaxRegime.SELLER_IOR_DDP: (True, True, True),
    TaxRegime.SELLER_LIABLE_LOW_VALUE: (False, True, True),
    TaxRegime.PLATFORM_COLLECTS: (True, False, False),
    TaxRegime.ASSUMED_WORST: (True, True, True),
}


def _as_int(value: object, name: str) -> int:
    if isinstance(value, float):
        raise CanonicalisationError(f"{name} 不能用 float(INV-16)")
    return int(dec(value))


def _item(
    key: str,
    value: int,
    rate: RateValue | None,
) -> CostItem:
    return CostItem(
        key=key,
        value_jpy=value,
        unit="JPY",
        source=rate.source if rate else "",
        fetched_at=rate.fetched_at if rate else None,
        status=rate.status if rate else ItemStatus.CONFIRMED,
        severity=rate.severity if rate else Severity.BLOCKING,
    )


def _unknown(missing: list[str], fx_rate_id: str, tax_regime: str) -> CostResult:
    return CostResult(
        status=ResultStatus.UNKNOWN,
        items=(),
        revenue=None,
        profit=None,
        margin=None,
        missing=tuple(missing),
        assumed=False,
        fx_rate_id=fx_rate_id,
        tax_regime=tax_regime,
    )


def compute(inp: CostInput) -> CostResult:
    """返回成本分项与利润。缺 BLOCKING 项时返回 UNKNOWN(INV-10)。"""
    card = inp.rate_card
    tax_regime = inp.tax.value
    fx_rate_id = inp.fx.source_id

    if inp.tax is TaxRegime.UNKNOWN:
        return _unknown(["tax_regime"], fx_rate_id, tax_regime)

    missing: list[str] = []
    for key in REQUIRED_CARD_KEYS:
        rate = card.get(key)
        if rate is None or rate.status is ItemStatus.MISSING or rate.value is None:
            missing.append(key)
    c3_rate = card.get(ITEM_C3)
    c3_from_table = (
        inp.ship_table is not None
        and inp.ship_table.price_for(inp.listing.weight_g) is not None
    )
    if not c3_from_table and (
        c3_rate is None or c3_rate.status is ItemStatus.MISSING or c3_rate.value is None
    ):
        missing.append(ITEM_C3)
    if missing:
        return _unknown(missing, fx_rate_id, tax_regime)

    fx = dec(inp.fx.rate)
    listing: ListingFacts = inp.listing
    assumptions: Assumptions = inp.assumptions
    charge_duty, charge_import_tax, seller_bears_output = _TAX_PROFILE[inp.tax]
    assumed = inp.tax is TaxRegime.ASSUMED_WORST

    def rate_of(key: str) -> Decimal:
        return dec(card[key].value)

    # --- c1 / c2 / c3 -----------------------------------------------------
    c1 = jpy(rate_of("c1_goods") * fx)
    c2 = jpy(rate_of("c2_domestic_ship") * fx)
    if c3_from_table:
        c3 = int(inp.ship_table.price_for(listing.weight_g))  # type: ignore[union-attr]
        c3_rate = c3_rate or RateValue(value=c3, severity=Severity.BLOCKING)
    else:
        c3 = jpy(c3_rate.value)  # type: ignore[union-attr]

    # --- c4 关税 / c5 输入消费税(以 c1+c3 为课税价格) ---------------------
    duty_base = c1 + c3
    c4 = jpy(rate_of("c4_customs_duty_rate") * duty_base) if charge_duty else 0
    c5_rate = card["c5_consumption_tax_rate"]
    consumption_rate = rate_of("c5_consumption_tax_rate")
    if charge_import_tax:
        shipment_value = (duty_base + c4) * max(1, assumptions.order_units)
        low_value_exempt = (
            inp.tax is TaxRegime.SELLER_LIABLE_LOW_VALUE
            and shipment_value <= _LOW_VALUE_THRESHOLD_JPY
        )
        c5 = 0 if low_value_exempt else jpy(consumption_rate * (duty_base + c4))
    else:
        c5 = 0

    # --- c6 通関费(按票分摊)/ c7 包材 ------------------------------------
    c6 = jpy(rate_of("c6_customs_fee") / max(1, assumptions.order_units))
    c7 = jpy(rate_of("c7_packaging"))

    landed = c1 + c2 + c3 + c4 + c5 + c6 + c7  # 到岸成本:佣金与退货损耗不并入

    # --- 营收:税込售价是否需要剔除销项税 ---------------------------------
    gross = listing.price_jpy + listing.buyer_shipping_fee_jpy
    revenue = jpy(gross / (1 + consumption_rate)) if seller_bears_output else jpy(gross)

    # --- c8 佣金 / c9 支付手续费 ------------------------------------------
    c8 = jpy(rate_of("c8_commission_rate") * listing.price_jpy)
    c9 = jpy(rate_of("c9_payment_fee_rate") * gross)

    # --- c10 退货损耗(期望值,已含退款对营收的扣减) ----------------------
    r = dec(assumptions.return_rate)
    rho = dec(assumptions.refund_commission_return)
    u = dec(assumptions.unsellable_ratio)
    loss_base = dec(revenue) + dec(assumptions.return_shipping_jpy) - rho * dec(c8)
    if assumptions.return_mode is ReturnMode.RETURN_TO_CN:
        loss_base -= (1 - u) * dec(c1)
    c10 = jpy(r * loss_base)

    # --- 可为零的三项(必须显式确认,缺省不猜) ----------------------------
    c11 = jpy(rate_of("c11_affiliate_rate") * listing.price_jpy) if "c11_affiliate_rate" in card else 0
    c12 = _as_int(card["c12_ad_per_unit"].value, "c12_ad_per_unit") if "c12_ad_per_unit" in card else 0
    c13 = _as_int(card["c13_promo_per_unit"].value, "c13_promo_per_unit") if "c13_promo_per_unit" in card else 0

    # --- c14 结算换汇 / c15 发出件损耗 / c16 样品摊销 ---------------------
    c14 = jpy(rate_of("c14_settlement_rate") * dec(revenue))
    c15 = jpy(rate_of("c15_loss_rate") * dec(landed))
    expected = max(1, listing.expected_sales)
    c16 = jpy(dec(listing.sample_cost_jpy) / expected)

    items = (
        _item(ITEM_C1, c1, card["c1_goods"]),
        _item(ITEM_C2, c2, card["c2_domestic_ship"]),
        _item(ITEM_C3, c3, c3_rate),
        _item(ITEM_C4, c4, card["c4_customs_duty_rate"]),
        _item(ITEM_C5, c5, c5_rate),
        _item(ITEM_C6, c6, card["c6_customs_fee"]),
        _item(ITEM_C7, c7, card["c7_packaging"]),
        _item(ITEM_C8, c8, card["c8_commission_rate"]),
        _item(ITEM_C9, c9, card["c9_payment_fee_rate"]),
        _item(ITEM_C10, c10, None),
        _item(ITEM_C11, c11, card.get("c11_affiliate_rate")),
        _item(ITEM_C12, c12, card.get("c12_ad_per_unit")),
        _item(ITEM_C13, c13, card.get("c13_promo_per_unit")),
        _item(ITEM_C14, c14, card["c14_settlement_rate"]),
        _item(ITEM_C15, c15, card["c15_loss_rate"]),
        _item(ITEM_C16, c16, None),
    )

    total_cost = sum(int(item.value_jpy or 0) for item in items)
    profit = revenue - total_cost
    margin = q4(Decimal(profit) / Decimal(revenue)) if revenue else None

    return CostResult(
        status=ResultStatus.COMPUTED,
        items=items,
        revenue=revenue,
        profit=profit,
        margin=margin,
        missing=(),
        assumed=assumed,
        fx_rate_id=fx_rate_id,
        tax_regime=tax_regime,
    )
