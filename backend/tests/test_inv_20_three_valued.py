"""INV-20: rule evaluation is three-valued. Removing a fact can only make the
outcome stricter, never open a door.

The property: for every subset of facts, the verdict is never ALLOW_AUTO when
the action is a red-light action — deleting a required fact turns MATCH into
UNKNOWN (HOLD), not into "no match".
"""

from __future__ import annotations

import itertools
import unittest

from crosspilot.core.decision import Decision, Severity, Tri
from crosspilot.core.facts import Facts
from crosspilot.gatekeeper.judge import judge
from crosspilot.gatekeeper.rules import rule

from .support import LISTER, NOW, PILOT, ruleset

FACTS = {
    "demand_signal": 0.81,
    "profit_margin": 0.32,
    "competition_gap": 0.44,
    "risk_score": 0.12,
}


def _subsets(items):
    for size in range(len(items) + 1):
        for combination in itertools.combinations(items, size):
            yield combination


class Inv20ThreeValued(unittest.TestCase):
    def test_rule_with_missing_fact_is_unknown(self):
        risky = rule(
            "RULE-MARGIN",
            severity=Severity.BLOCK,
            predicate=lambda facts: facts["profit_margin"] < 0.25,
            scope=("ACT-SELECT",),
            requires_facts=("profit_margin",),
        )
        self.assertIs(risky.evaluate(Facts(demand_signal=1.0)), Tri.UNKNOWN)
        self.assertIs(risky.evaluate(Facts(profit_margin=0.10)), Tri.MATCH)
        self.assertIs(risky.evaluate(Facts(profit_margin=0.90)), Tri.NO_MATCH)

    def test_no_fact_subset_ever_yields_allow(self):
        rs = ruleset(
            rules=[
                rule(
                    "RULE-SELECT-BLOCK",
                    severity=Severity.BLOCK,
                    predicate=lambda facts: facts["risk_score"] > 0.5,
                    scope=("ACT-SELECT",),
                    requires_facts=("risk_score",),
                ),
                rule(
                    "RULE-SELECT-WARN",
                    severity=Severity.WARN,
                    predicate=lambda facts: facts["competition_gap"] < 0.2,
                    scope=("ACT-SELECT",),
                    requires_facts=("competition_gap",),
                ),
            ]
        )
        for subset in _subsets(FACTS):
            facts = Facts({name: FACTS[name] for name in subset})
            with self.subTest(facts=subset):
                verdict = judge(PILOT, "ACT-SELECT", facts, rs, NOW)
                self.assertIsNot(verdict.decision, Decision.ALLOW_AUTO)

    def test_complete_facts_produce_a_human_decision_not_an_auto_pass(self):
        rs = ruleset()
        verdict = judge(PILOT, "ACT-LIST-CREATE", Facts({}), rs, NOW)
        # No rules and no required facts known -> HOLD, never ALLOW.
        self.assertIs(verdict.decision, Decision.HOLD)

    def test_deleting_a_fact_moves_block_to_hold(self):
        rs = ruleset(
            rules=[
                rule(
                    "RULE-X",
                    severity=Severity.BLOCK,
                    predicate=lambda facts: facts["risk_score"] > 0.5,
                    scope=("ACT-LIST-CREATE",),
                    requires_facts=("risk_score",),
                )
            ]
        )
        full = Facts(risk_score=0.9)
        self.assertIs(judge(LISTER, "ACT-LIST-CREATE", full, rs, NOW).decision, Decision.BLOCK)
        self.assertIs(
            judge(LISTER, "ACT-LIST-CREATE", Facts({}), rs, NOW).decision,
            Decision.HOLD,
        )


if __name__ == "__main__":
    unittest.main()
