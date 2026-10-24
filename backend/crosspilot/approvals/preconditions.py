"""Preconditions PC-* (04 §5.2).

A frozen payload only proves the bytes were not edited; it says nothing about
whether the facts behind them still hold. These checks are what turns "approved
on Monday" into "still true right now".

Every check is a pure comparison of two :class:`FactSnapshot` values plus a
clock and the guardrail tolerances. There is no I/O here, so the same code runs
in the nightly freshness scan and inside the Tool Gate at the last moment
(04 §5.2 trigger 1 and 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable, Mapping

from ..core.errors import ToolGateError
from ..core.money import dec, q4


@dataclass(frozen=True, slots=True)
class Guardrails:
    """Tolerances that only ever move in the stricter direction (04 §8)."""

    fx_deviation_max: Decimal = Decimal("0.03")
    source_price_deviation_max: Decimal = Decimal("0.05")
    fx_max_age_hours: int = 24
    source_max_age_days: int = 7


@dataclass(frozen=True, slots=True)
class FactSnapshot:
    """The facts an approval was granted on, and the same facts re-read now.

    One type serves both roles so that a missing attribute is a missing *fact*
    rather than a silently defaulted value.
    """

    payload_hash: str = ""
    fx_rate: Decimal | None = None
    fx_fetched_at: datetime | None = None
    source_confirmed_at: datetime | None = None
    source_price_cny: Decimal | None = None
    margin: Decimal | None = None
    margin_floor: Decimal | None = None
    cost_missing_blocking: tuple[str, ...] = ()
    price_jpy: int | None = None
    cost_floor_jpy: int | None = None
    ruleset_version: str = ""
    rules_block: bool = False
    g0_allowed: bool = True
    shop_profile_version: int = 0
    direction_version: int = 0
    direction_still_satisfied: bool = True
    asset_hashes: tuple[str, ...] = ()
    tax_regime: str = "UNKNOWN"
    tax_effective_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class CheckResult:
    pc: str
    passed: bool
    was: str = ""
    now: str = ""
    detail: str = ""

    def as_failure(self) -> dict[str, str]:
        return {"pc": self.pc, "was": self.was, "now": self.now, "detail": self.detail}


def _fmt(value: object) -> str:
    if isinstance(value, Decimal):
        return format(q4(value), "f")
    return "" if value is None else str(value)


def _pc_payload(
    snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails
) -> CheckResult:
    return CheckResult(
        pc="PC-PAYLOAD",
        passed=bool(snap.payload_hash) and snap.payload_hash == cur.payload_hash,
        was=snap.payload_hash[:12],
        now=cur.payload_hash[:12],
        detail="payload hash differs from the approved one",
    )


def _pc_fx_fresh(
    snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails
) -> CheckResult:
    if cur.fx_fetched_at is None:
        return CheckResult("PC-FX-FRESH", False, "", "", "fx rate has no fetch time")
    age_hours = (now - cur.fx_fetched_at).total_seconds() / 3600
    return CheckResult(
        pc="PC-FX-FRESH",
        passed=age_hours <= g.fx_max_age_hours,
        was=f"{snap.fx_rate if snap.fx_rate is not None else ''}",
        now=f"{age_hours:.1f}h old",
        detail=f"fx rate older than {g.fx_max_age_hours} h",
    )


def _pc_source_fresh(
    snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails
) -> CheckResult:
    if cur.source_confirmed_at is None:
        return CheckResult("PC-SOURCE-FRESH", False, "", "", "source has no confirmation time")
    age_days = (now - cur.source_confirmed_at).total_seconds() / 86400
    return CheckResult(
        pc="PC-SOURCE-FRESH",
        passed=age_days <= g.source_max_age_days,
        now=f"{age_days:.1f}d old",
        detail=f"source confirmation older than {g.source_max_age_days} d",
    )


def _pc_fx(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    if snap.fx_rate is None or cur.fx_rate is None or dec(snap.fx_rate) == 0:
        return CheckResult("PC-FX", False, _fmt(snap.fx_rate), _fmt(cur.fx_rate), "fx rate unknown")
    deviation = abs(dec(cur.fx_rate) - dec(snap.fx_rate)) / dec(snap.fx_rate)
    return CheckResult(
        pc="PC-FX",
        passed=deviation <= g.fx_deviation_max,
        was=_fmt(snap.fx_rate),
        now=_fmt(cur.fx_rate),
        detail=f"fx moved {deviation:.2%} (limit {g.fx_deviation_max:.2%})",
    )


def _pc_cost(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    if cur.cost_missing_blocking:
        return CheckResult(
            "PC-COST",
            False,
            now=",".join(cur.cost_missing_blocking),
            detail="a BLOCKING cost item became MISSING",
        )
    if cur.margin is None:
        return CheckResult("PC-COST", False, detail="margin is UNKNOWN")
    floor = cur.margin_floor if cur.margin_floor is not None else snap.margin_floor
    if floor is not None and q4(cur.margin) < q4(floor):
        return CheckResult(
            "PC-COST",
            False,
            was=_fmt(snap.margin),
            now=_fmt(cur.margin),
            detail=f"margin fell below the floor {_fmt(floor)}",
        )
    return CheckResult("PC-COST", True, was=_fmt(snap.margin), now=_fmt(cur.margin))


def _pc_price_floor(
    snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails
) -> CheckResult:
    if cur.price_jpy is None or cur.cost_floor_jpy is None:
        return CheckResult("PC-PRICE-FLOOR", False, detail="price or floor price unknown")
    return CheckResult(
        "PC-PRICE-FLOOR",
        cur.price_jpy > cur.cost_floor_jpy,
        was=str(snap.price_jpy),
        now=str(cur.price_jpy),
        detail="price is at or below the zero-profit floor",
    )


def _pc_source(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    if snap.source_price_cny is None or cur.source_price_cny is None:
        return CheckResult("PC-SOURCE", False, detail="source price unknown")
    if dec(snap.source_price_cny) == 0:
        return CheckResult("PC-SOURCE", False, detail="source price was zero")
    deviation = abs(dec(cur.source_price_cny) - dec(snap.source_price_cny)) / dec(
        snap.source_price_cny
    )
    return CheckResult(
        "PC-SOURCE",
        deviation <= g.source_price_deviation_max,
        was=_fmt(snap.source_price_cny),
        now=_fmt(cur.source_price_cny),
        detail=f"source price moved {deviation:.2%}",
    )


def _pc_rules(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    # A new rule set alone is not a failure; a new *block* for this object is.
    changed = snap.ruleset_version != cur.ruleset_version
    return CheckResult(
        "PC-RULES",
        not (changed and cur.rules_block),
        was=snap.ruleset_version,
        now=cur.ruleset_version,
        detail="the new rule set blocks this object",
    )


def _pc_g0(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    return CheckResult("PC-G0", bool(cur.g0_allowed), detail="category is no longer allowed (G0)")


def _pc_shop(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    return CheckResult(
        "PC-SHOP",
        snap.shop_profile_version == cur.shop_profile_version,
        was=str(snap.shop_profile_version),
        now=str(cur.shop_profile_version),
        detail="shop profile changed (disclosure / shipping / dispatch days)",
    )


def _pc_direction(
    snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails
) -> CheckResult:
    changed = snap.direction_version != cur.direction_version
    return CheckResult(
        "PC-DIRECTION",
        not (changed and not cur.direction_still_satisfied),
        was=str(snap.direction_version),
        now=str(cur.direction_version),
        detail="a newer direction card no longer covers this item",
    )


def _pc_asset(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    return CheckResult(
        "PC-ASSET",
        snap.asset_hashes == cur.asset_hashes,
        was=",".join(h[:8] for h in snap.asset_hashes),
        now=",".join(h[:8] for h in cur.asset_hashes),
        detail="an approved asset file changed (new version needs consent 2 again)",
    )


def _pc_tax(snap: FactSnapshot, cur: FactSnapshot, now: datetime, g: Guardrails) -> CheckResult:
    if cur.tax_regime in ("", "UNKNOWN"):
        return CheckResult("PC-TAX", False, was=snap.tax_regime, now=cur.tax_regime, detail="tax regime unknown")
    if cur.tax_regime != snap.tax_regime:
        return CheckResult(
            "PC-TAX", False, was=snap.tax_regime, now=cur.tax_regime, detail="tax regime changed"
        )
    if cur.tax_effective_until is not None and now > cur.tax_effective_until:
        return CheckResult(
            "PC-TAX", False, now=str(cur.tax_effective_until), detail="tax regime window expired (U-3b)"
        )
    return CheckResult("PC-TAX", True, was=snap.tax_regime, now=cur.tax_regime)


_CHECKERS: Mapping[
    str, Callable[[FactSnapshot, FactSnapshot, datetime, Guardrails], CheckResult]
] = {
    "PC-PAYLOAD": _pc_payload,
    "PC-FX-FRESH": _pc_fx_fresh,
    "PC-SOURCE-FRESH": _pc_source_fresh,
    "PC-FX": _pc_fx,
    "PC-COST": _pc_cost,
    "PC-PRICE-FLOOR": _pc_price_floor,
    "PC-SOURCE": _pc_source,
    "PC-RULES": _pc_rules,
    "PC-G0": _pc_g0,
    "PC-SHOP": _pc_shop,
    "PC-DIRECTION": _pc_direction,
    "PC-ASSET": _pc_asset,
    "PC-TAX": _pc_tax,
}


def evaluate(
    snapshot: FactSnapshot,
    current: FactSnapshot,
    now: datetime,
    *,
    preconditions: tuple[str, ...] | None = None,
    guardrails: Guardrails | None = None,
) -> tuple[CheckResult, ...]:
    g = guardrails or Guardrails()
    names = preconditions if preconditions is not None else tuple(_CHECKERS)
    results: list[CheckResult] = []
    for name in names:
        checker = _CHECKERS.get(name)
        if checker is None:
            raise KeyError(f"unknown precondition: {name}")
        results.append(checker(snapshot, current, now, g))
    return tuple(results)


def failures(results: tuple[CheckResult, ...]) -> tuple[CheckResult, ...]:
    return tuple(r for r in results if not r.passed)


def assert_all_pass(results: tuple[CheckResult, ...], *, successor_id: str | None = None) -> None:
    bad = failures(results)
    if not bad:
        return
    raise ToolGateError(
        "PRECONDITION_FAILED",
        "; ".join(f"{r.pc} ({r.was} -> {r.now})" for r in bad),
        failed=[r.as_failure() for r in bad],
        successor_id=successor_id,
    )


#: Human-readable names used by the approval card (SCR-06).
PC_LABELS: Mapping[str, str] = {
    "PC-PAYLOAD": "载荷未被改写",
    "PC-FX-FRESH": "汇率新鲜",
    "PC-SOURCE-FRESH": "货源确认新鲜",
    "PC-FX": "汇率偏离在阈值内",
    "PC-COST": "毛利仍达标",
    "PC-PRICE-FLOOR": "售价高于成本地板价",
    "PC-SOURCE": "货源价未变",
    "PC-RULES": "新规则未阻断",
    "PC-G0": "类目仍准售",
    "PC-SHOP": "店铺档案未变",
    "PC-DIRECTION": "方向卡仍覆盖",
    "PC-ASSET": "素材未改",
    "PC-TAX": "税口径仍有效",
}


__all__ = [
    "CheckResult",
    "FactSnapshot",
    "Guardrails",
    "PC_LABELS",
    "assert_all_pass",
    "evaluate",
    "failures",
]
