"""只读接口的处理器(纯函数,无框架依赖)。

FastAPI 适配层(`main.py`)与标准库适配层(`server.py`)都只是把这里的 dict 变成 HTTP。
CI 不装 FastAPI 也能测业务,这是 02-设计 §1 的接缝约定。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crosspilot.costing import (
    Assumptions,
    CostInput,
    FxRate,
    ItemStatus,
    ListingFacts,
    RateValue,
    ReturnMode,
    Severity,
    TaxRegime,
    compute,
)

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "sample"


def _read(sample_dir: Path, name: str) -> dict[str, Any] | None:
    try:
        return json.loads((sample_dir / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def health() -> dict[str, str]:
    return {"status": "ok"}


def today(sample_dir: Path | None = None) -> dict[str, Any]:
    data = _read(sample_dir or SAMPLE_DIR, "today.json") or {}
    return {
        "pending_approvals": int(data.get("pending_approvals", 0)),
        "readiness": data.get("readiness", {"items": [], "missing": []}),
        "reminders": data.get("reminders", []),
    }


def _rate(raw: dict[str, Any]) -> RateValue:
    return RateValue(
        value=raw.get("value"),
        unit=raw.get("unit", "JPY"),
        source=raw.get("source", ""),
        status=ItemStatus(raw.get("status", "CONFIRMED")),
        severity=Severity(raw.get("severity", "BLOCKING")),
    )


def _to_input(raw: dict[str, Any]) -> CostInput:
    fx = raw["fx"]
    listing = raw["listing"]
    assumptions = raw["assumptions"]
    return CostInput(
        rate_card={key: _rate(value) for key, value in raw["rate_card"].items()},
        fx=FxRate(rate=fx["rate"], ref_date=__import__("datetime").date.fromisoformat(fx["ref_date"]), source_id=fx["source_id"]),
        tax=TaxRegime(raw.get("tax", "UNKNOWN")),
        listing=ListingFacts(
            price_jpy=listing["price_jpy"],
            buyer_shipping_fee_jpy=listing.get("buyer_shipping_fee_jpy", 0),
            weight_g=listing.get("weight_g", 0),
            sample_cost_jpy=listing.get("sample_cost_jpy", 0),
            expected_sales=listing.get("expected_sales", 0),
        ),
        assumptions=Assumptions(
            return_rate=assumptions.get("return_rate", "0"),
            refund_commission_return=assumptions.get("refund_commission_return", "0"),
            unsellable_ratio=assumptions.get("unsellable_ratio", "0"),
            return_shipping_jpy=assumptions.get("return_shipping_jpy", 0),
            return_mode=ReturnMode(assumptions.get("return_mode", "DISPOSE_JP")),
            order_units=assumptions.get("order_units", 1),
        ),
    )


def candidates(sample_dir: Path | None = None) -> dict[str, Any]:
    data = _read(sample_dir or SAMPLE_DIR, "candidates.json")
    if data is None:
        return {"items": [], "notes": ["样例数据缺失,请检查 backend/data/sample/candidates.json"]}

    items = []
    for raw in data.get("items", []):
        result = compute(_to_input(raw))
        items.append(
            {
                "id": raw["id"],
                "title": raw["title"],
                "category": raw.get("category", ""),
                "price_jpy": raw.get("price_jpy"),
                "status": result.status.value,
                "revenue": result.revenue,
                "profit": result.profit,
                "margin": format(result.margin, "f") if result.margin is not None else None,
                "missing": list(result.missing),
                "tax_regime": result.tax_regime,
                "fx_rate_id": result.fx_rate_id,
                "cost_items": [
                    {
                        "key": item.key,
                        "value_jpy": item.value_jpy,
                        "source": item.source,
                        "status": item.status.value,
                        "severity": item.severity.value,
                    }
                    for item in result.items
                ],
            }
        )
    return {"items": items}
