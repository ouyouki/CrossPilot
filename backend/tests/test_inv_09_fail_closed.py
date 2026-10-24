"""INV-9: a broken or stale decision engine yields HOLD, never ALLOW."""

from __future__ import annotations

import unittest

from crosspilot.core.decision import Decision, Severity
from crosspilot.core.errors import ToolGateError
from crosspilot.core.facts import Facts
from crosspilot.gatekeeper.judge import judge
from crosspilot.gatekeeper.rules import rule
from crosspilot.toolgate.gate import ToolGate

from .support import (
    LISTER,
    NOW,
    consent2_approval,
    consent2_facts,
    execution_call,
    harness,
    ruleset,
)


class _BrokenFacts(Facts):
    """Facts whose accessor fails: simulates a corrupted fact store."""

    def is_known(self, name: str) -> bool:  # noqa: D401 - deliberate failure
        raise RuntimeError("fact store unavailable")


class Inv09FailClosed(unittest.TestCase):
    def _gate_with(self, provider):
        h = harness()
        h.gate = ToolGate(
            repo=h.repo,
            approvals=h.service,
            audit=h.audit,
            clock=h.clock,
            ruleset_provider=provider,
        )
        return h

    def test_missing_ruleset_holds(self):
        h = self._gate_with(lambda: None)
        h.approve(h.service.create(consent2_approval()))
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(ctx.exception.code, "HELD_UNKNOWN")
        self.assertEqual(executed, [])

    def test_stale_ruleset_holds_with_age(self):
        h = harness(valid_days=-2)
        h.approve(h.service.create(consent2_approval()))
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(ctx.exception.code, "HELD_UNKNOWN")
        self.assertIn("expired", ctx.exception.detail.lower())
        self.assertEqual(executed, [])

    def test_crashing_rule_holds(self):
        h = harness(
            rules=[
                rule(
                    "RULE-BOOM",
                    severity=Severity.BLOCK,
                    predicate=lambda facts: 1 / 0,
                    scope=("ACT-LIST-CREATE",),
                )
            ]
        )
        h.approve(h.service.create(consent2_approval()))

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), lambda approval: None)

        self.assertEqual(ctx.exception.code, "HELD_UNKNOWN")

    def test_judge_returns_hold_not_allow_on_engine_fault(self):
        verdict = judge(LISTER, "ACT-LIST-CREATE", _BrokenFacts(), ruleset(), NOW)
        self.assertIs(verdict.decision, Decision.HOLD)
        self.assertEqual(verdict.reasons[0].rule_id, "judge_error")

    def test_judge_returns_hold_without_ruleset(self):
        verdict = judge(LISTER, "ACT-LIST-CREATE", consent2_facts(), None, NOW)
        self.assertIs(verdict.decision, Decision.HOLD)

    def test_governance_action_does_not_need_a_fresh_ruleset(self):
        # 04 §2.1: otherwise a stale rule set could never be renewed.
        verdict = judge(LISTER, "ACT-RULESET-RENEW", Facts(), None, NOW)
        self.assertIs(verdict.decision, Decision.ALLOW_AUTO)


if __name__ == "__main__":
    unittest.main()
