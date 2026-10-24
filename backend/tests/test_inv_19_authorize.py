"""INV-19: the gate authorizes the actor before anything else happens.

Agents may call only AUTO actions that are in their own tool whitelist;
HUMAN_INITIATED actions need a person with the right role; nothing may call a
decision as a tool (AC-06, AC-39).
"""

from __future__ import annotations

import unittest

from crosspilot.approvals.service import ApprovalDecision
from crosspilot.audit.log import AuditDecision
from crosspilot.core.errors import ToolGateError
from crosspilot.toolgate.gate import ToolCall

from .support import (
    OWNER,
    PILOT,
    SCOUT,
    SHOP,
    WORKER,
    consent2_approval,
    harness,
)


class Inv19Authorize(unittest.TestCase):
    def test_agent_cannot_call_approval_decide(self):
        h = harness()
        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(
                ToolCall(actor=SCOUT, tool="approval.decide", shop_id=SHOP),
                lambda approval: None,
            )
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")

    def test_agent_cannot_use_a_tool_outside_its_whitelist(self):
        h = harness()
        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(
                ToolCall(actor=PILOT, tool="listing.build_checklist", shop_id=SHOP),
                lambda approval: None,
            )
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")

    def test_whitelisted_auto_action_is_allowed(self):
        h = harness()
        executed: list[object] = []
        h.gate.call(
            ToolCall(actor=SCOUT, tool="score.run", shop_id=SHOP),
            lambda approval: executed.append(approval),
        )
        self.assertEqual(executed, [None])
        self.assertIs(h.audit.entries()[-1].decision, AuditDecision.ALLOWED)

    def test_system_cannot_run_human_initiated_action(self):
        h = harness()
        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(
                ToolCall(actor=WORKER, tool="import.parse_file", shop_id=SHOP),
                lambda approval: None,
            )
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")

    def test_human_needs_the_matching_role_to_decide(self):
        h = harness()
        pending = h.service.submit(h.service.create(consent2_approval()).id, now=h.clock.now())
        with self.assertRaises(ToolGateError) as ctx:
            h.service.decide(
                pending.id,
                actor=OWNER,  # consent 2 is an Operator decision
                if_match_version=pending.version,
                payload_hash=pending.payload_hash,
                decision=ApprovalDecision.APPROVE,
            )
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")

    def test_refusals_are_audited(self):
        h = harness()
        with self.assertRaises(ToolGateError):
            h.gate.call(
                ToolCall(actor=PILOT, tool="listing.build_checklist", shop_id=SHOP),
                lambda approval: None,
            )
        self.assertIs(h.audit.entries()[-1].decision, AuditDecision.DENIED)


if __name__ == "__main__":
    unittest.main()
