"""价值对象与枚举(02-设计 §3)。金额一律整型 JPY 或 Decimal,不接受 float(INV-16)。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping

from ..core.money import CanonicalisationError


class Severity(str, Enum):
    BLOCKING = "BLOCKING"
    OPTIONAL_ZERO = "OPTIONAL_ZERO"


class ItemStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    ESTIMATED = "ESTIMATED"
    MISSING = "MISSING"


class TaxRegime(str, Enum):
    """03 §3.1:单一枚举,互斥。UNKNOWN 时利润不可算。"""

    DE_MINIMIS_EXEMPT = "DE_MINIMIS_EXEMPT"
    SELLER_IOR_DDP = "SELLER_IOR_DDP"
    SELLER_LIABLE_LOW_VALUE = "SELLER_LIABLE_LOW_VALUE"
    PLATFORM_COLLECTS = "PLATFORM_COLLECTS"
    ASSUMED_WORST = "ASSUMED_WORST"
    UNKNOWN = "UNKNOWN"


class ResultStatus(str, Enum):
    COMPUTED = "COMPUTED"
    UNKNOWN = "UNKNOWN"


class ReturnMode(str, Enum):
    RETURN_TO_CN = "RETURN_TO_CN"
    DISPOSE_JP = "DISPOSE_JP"
    REFUND_ONLY = "REFUND_ONLY"


def _check_no_float(value: object, field_name: str) -> None:
    if isinstance(value, float):
        raise CanonicalisationError(
            f"{field_name} 不能用 float(INV-16);请传 int 或 Decimal"
        )


@dataclass(frozen=True, slots=True)
class RateValue:
    """费率卡里的一项。status=MISSING 时 value 必须为空。"""

    value: Decimal | int | None = None
    unit: str = "JPY"
    source: str = ""
    fetched_at: datetime | None = None
    status: ItemStatus = ItemStatus.CONFIRMED
    severity: Severity = Severity.BLOCKING

    def __post_init__(self) -> None:
        _check_no_float(self.value, "RateValue.value")
        if self.status is ItemStatus.MISSING and self.value is not None:
            raise ValueError("status=MISSING 的费率项不能带 value(不许用默认值补)")


@dataclass(frozen=True, slots=True)
class FxRate:
    rate: Decimal | int
    ref_date: date
    source_id: str

    def __post_init__(self) -> None:
        _check_no_float(self.rate, "FxRate.rate")


@dataclass(frozen=True, slots=True)
class IntlShipTable:
    """(最大重量 g, 价格 JPY),按重量升序;超出最大档视为缺档。"""

    tiers: tuple[tuple[int, int], ...] = ()

    def price_for(self, weight_g: int) -> int | None:
        for max_g, price in sorted(self.tiers):
            if weight_g <= max_g:
                return price
        return None


@dataclass(frozen=True, slots=True)
class Assumptions:
    return_rate: Decimal | int = Decimal("0")
    refund_commission_return: Decimal | int = Decimal("0")  # ρ,缺省 0 且 UNVERIFIED
    unsellable_ratio: Decimal | int = Decimal("0")
    return_shipping_jpy: int = 0
    return_mode: ReturnMode = ReturnMode.DISPOSE_JP
    order_units: int = 1  # 每票件数(通関费分摊、低价值门槛)

    def __post_init__(self) -> None:
        for name in ("return_rate", "refund_commission_return", "unsellable_ratio"):
            _check_no_float(getattr(self, name), f"Assumptions.{name}")


@dataclass(frozen=True, slots=True)
class ListingFacts:
    price_jpy: int
    buyer_shipping_fee_jpy: int = 0
    weight_g: int = 0
    sample_cost_jpy: int = 0
    expected_sales: int = 0
    hs_class: str = ""

    def __post_init__(self) -> None:
        for name in ("price_jpy", "buyer_shipping_fee_jpy", "weight_g", "sample_cost_jpy", "expected_sales"):
            _check_no_float(getattr(self, name), f"ListingFacts.{name}")


@dataclass(frozen=True, slots=True)
class CostInput:
    rate_card: Mapping[str, RateValue]
    fx: FxRate
    tax: TaxRegime
    listing: ListingFacts
    assumptions: Assumptions = field(default_factory=Assumptions)
    ship_table: IntlShipTable | None = None
    tax_effective_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class CostItem:
    key: str
    value_jpy: int | None
    unit: str
    source: str
    fetched_at: datetime | None
    status: ItemStatus
    severity: Severity


@dataclass(frozen=True, slots=True)
class CostResult:
    status: ResultStatus
    items: tuple[CostItem, ...]
    revenue: int | None
    profit: int | None
    margin: Decimal | None
    missing: tuple[str, ...]
    assumed: bool
    fx_rate_id: str
    tax_regime: str
