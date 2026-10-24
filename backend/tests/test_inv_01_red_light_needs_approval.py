"""INV-1: a REQUIRE_HUMAN action never executes without an APPROVED approval."""

from __future__ import annotations

import unittest

from crosspilot.core.errors import ToolGateError
from crosspilot.audit.log import AuditDecision

from .support import consent2_approval, execution_call, harness


class Inv01RedLightNeedsApproval(unittest.TestCase):
    def test_no_approval_means_no_execution(self):
        h = harness()
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id=None), executed.append)

        self.assertEqual(ctx.exception.code, "NOT_APPROVED")
        self.assertEqual(executed, [])
        self.assertEqual(tuple(h.repo.all()), ())
        self.assertTrue(
            any(e.decision is AuditDecision.DENIED for e in h.audit.entries()),
            "a refused call must be audited (INV-11)",
        )

    def test_pending_approval_is_not_approval(self):
        h = harness()
        h.service.submit(h.service.create(consent2_approval()).id, now=h.clock.now())
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(ctx.exception.code, "NOT_APPROVED")
        self.assertEqual(executed, [])

    def test_approved_then_executed_and_consumed_once(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        executed: list[object] = []

        h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(len(executed), 1)
        self.assertEqual(h.repo.get("ap-1").status.value, "EXECUTED")

    def test_blocked_verdict_never_executes(self):
        from crosspilot.core.decision import Severity
        from crosspilot.gatekeeper.rules import rule

        h = harness(
            rules=[
                rule(
                    "RULE-TEST-BLOCK",
                    severity=Severity.BLOCK,
                    predicate=lambda facts: True,
                    scope=("ACT-LIST-CREATE",),
                )
            ]
        )
        h.approve(h.service.create(consent2_approval()))
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(ctx.exception.code, "BLOCKED")
        self.assertEqual(executed, [])
        # A BLOCK is not an approval; the approval stays unconsumed.
        self.assertEqual(h.repo.get("ap-1").status.value, "APPROVED")


if __name__ == "__main__":
    unittest.main()
