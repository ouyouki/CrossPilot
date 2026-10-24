"""INV-7: an action that is not in the registry is refused and audited —
and no approval is created for it."""

from __future__ import annotations

import unittest

from crosspilot.audit.log import AuditDecision
from crosspilot.core.errors import ToolGateError
from crosspilot.gatekeeper.judge import judge
from crosspilot.core.facts import Facts
from crosspilot.toolgate.gate import ToolCall

from .support import LISTER, NOW, OWNER, SHOP, harness, ruleset


class Inv07UnregisteredAction(unittest.TestCase):
    def test_judge_refuses_unknown_action(self):
        with self.assertRaises(ToolGateError) as ctx:
            judge(OWNER, "ACT-NOT-REGISTERED", Facts(), ruleset(), NOW)
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")
        self.assertEqual(ctx.exception.http_status, 403)

    def test_gate_refuses_unknown_tool_and_audits(self):
        h = harness()
        call = ToolCall(actor=LISTER, tool="listing.teleport", shop_id=SHOP)

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(call, lambda approval: None)

        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")
        self.assertEqual(tuple(h.repo.all()), (), "no approval may be created")
        denials = [e for e in h.audit.entries() if e.decision is AuditDecision.DENIED]
        self.assertEqual(len(denials), 1)
        self.assertEqual(denials[0].details["code"], "ACTION_FORBIDDEN")

    def test_tool_cannot_lie_about_its_action(self):
        h = harness()
        call = ToolCall(
            actor=LISTER,
            tool="listing.build_checklist",
            shop_id=SHOP,
            action="ACT-SELECT",  # mismatch with the registered action
        )
        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(call, lambda approval: None)
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
