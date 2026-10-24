"""Rule set and three-valued evaluation (04 §3).

A rule declares the facts it needs. If any of them is unknown the evaluation is
``UNKNOWN``, never ``NO_MATCH`` — that single decision is what makes INV-20 hold:
deleting a fact can turn a MATCH into UNKNOWN (HOLD) but can never turn it into
a pass.

A matcher that raises is also ``UNKNOWN``: a broken rule must not be read as
"rule not triggered" (INV-9).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ..core.decision import Severity, Tri
from ..core.facts import Facts


class Freshness(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    #: The rule family has no external data source in this phase (04 §3.3).
    #: It is *not* the same as "fresh", and it is not a service denial either.
    NOT_INTEGRATED = "NOT_INTEGRATED"


Predicate = Callable[[Facts], bool]


@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    severity: Severity
    #: Action names this rule applies to; ``("*",)`` means every action.
    scope: tuple[str, ...]
    requires_facts: tuple[str, ...]
    predicate: Predicate
    layer: str = "CORE"
    version: str = "1"
    #: UNVERIFIED rules may only make things stricter; the engine has no path in
    #: which a rule can *permit* anything, so this flag is carried for reporting.
    verified: bool = True
    source: str = ""
    rewrite_hint: str = ""

    def applies_to(self, action_name: str) -> bool:
        return "*" in self.scope or action_name in self.scope

    def evaluate(self, facts: Facts) -> Tri:
        missing = [name for name in self.requires_facts if not facts.is_known(name)]
        if missing:
            return Tri.UNKNOWN
        try:
            return Tri.MATCH if self.predicate(facts) else Tri.NO_MATCH
        except Exception:  # a rule that cannot run is unknown, not "no match"
            return Tri.UNKNOWN

    def matched_snippet(self, facts: Facts) -> str | None:
        """Best-effort hit text for the report; never used for the decision."""
        for name in self.requires_facts:
            value = facts.get_known(name, None)
            if isinstance(value, str) and value:
                return value
        return None


@dataclass(frozen=True, slots=True)
class RuleOutcome:
    rule: Rule
    tri: Tri


class RuleSet:
    """One published, versioned bundle of rules (06 §1 ``rulesets``)."""

    __slots__ = ("version", "published_at", "valid_until", "rules", "_by_action")

    def __init__(
        self,
        *,
        version: str,
        published_at: datetime | None = None,
        valid_until: datetime | None = None,
        rules: Iterable[Rule] = (),
    ) -> None:
        self.version = version
        self.published_at = published_at
        self.valid_until = valid_until
        self.rules: tuple[Rule, ...] = tuple(rules)
        index: dict[str, list[Rule]] = {}
        for rule in self.rules:
            for scope in rule.scope:
                index.setdefault(scope, []).append(rule)
        self._by_action: Mapping[str, list[Rule]] = index

    # -- freshness --------------------------------------------------------
    def freshness(self, now: datetime) -> Freshness:
        if not self.version:
            return Freshness.NOT_INTEGRATED
        if self.valid_until is None:
            return Freshness.NOT_INTEGRATED
        return Freshness.FRESH if now <= self.valid_until else Freshness.STALE

    def stale_hours(self, now: datetime) -> int:
        if self.valid_until is None:
            return 0
        delta = now - self.valid_until
        return max(0, int(delta.total_seconds() // 3600))

    def expired(self, now: datetime) -> bool:
        return self.freshness(now) is not Freshness.FRESH

    # -- evaluation -------------------------------------------------------
    def applicable(self, action_name: str) -> tuple[Rule, ...]:
        seen: dict[str, Rule] = {}
        for rule in self._by_action.get("*", ()):
            seen[rule.rule_id] = rule
        for rule in self._by_action.get(action_name, ()):
            seen[rule.rule_id] = rule
        return tuple(seen.values())

    def evaluate(self, action_name: str, facts: Facts) -> tuple[RuleOutcome, ...]:
        return tuple(RuleOutcome(rule, rule.evaluate(facts)) for rule in self.applicable(action_name))


def rule(
    rule_id: str,
    *,
    severity: Severity,
    predicate: Predicate,
    scope: tuple[str, ...] = ("*",),
    requires_facts: tuple[str, ...] = (),
    **kwargs: Any,
) -> Rule:
    return Rule(
        rule_id=rule_id,
        severity=severity,
        scope=scope,
        requires_facts=requires_facts,
        predicate=predicate,
        **kwargs,
    )


def empty_ruleset(*, version: str = "test-1", valid_until: datetime | None = None) -> RuleSet:
    return RuleSet(version=version, rules=(), valid_until=valid_until)


__all__ = ["Freshness", "Predicate", "Rule", "RuleOutcome", "RuleSet", "empty_ruleset", "rule"]
