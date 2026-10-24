"""INV-17: an approval is single-use and bound to exactly one object.

The execution request carries ``approval_id`` + subject ids + payload hash; all
three must agree with the approval, and the APPROVED -> EXECUTING transition is
a compare-and-set, so a second worker cannot reuse the same approval.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from crosspilot.approvals.model import ApprovalError
from crosspilot.approvals.state_machine import ApprovalStatus
from crosspilot.core.errors import ToolGateError

from .support import SHOP, consent2_approval, execution_call, harness


class Inv17ApprovalBinding(unittest.TestCase):
    def test_other_subject_is_refused(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(
                execution_call(approval_id="ap-1", subject="cand-2"), executed.append
            )

        self.assertEqual(ctx.exception.code, "APPROVAL_MISMATCH")
        self.assertEqual(executed, [])
        # The approval was not consumed: it can still be used on its own subject.
        self.assertEqual(h.repo.get("ap-1").status, ApprovalStatus.APPROVED)

    def test_other_shop_is_refused(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        call = replace(execution_call(approval_id="ap-1"), shop_id="shop-2")

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(call, lambda approval: None)

        self.assertEqual(ctx.exception.code, "APPROVAL_MISMATCH")

    def test_double_execution_is_refused(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        h.gate.call(execution_call(approval_id="ap-1"), lambda approval: None)
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(ctx.exception.code, "APPROVAL_ALREADY_CONSUMED")
        self.assertEqual(executed, [])

    def test_subject_refs_must_be_ids_not_queries(self):
        with self.assertRaises(ApprovalError):
            _ = consent2_approval(subject="cand-1?price=100")
        with self.assertRaises(ApprovalError):
            _ = consent2_approval(subject="cand-1, cand-2")
        with self.assertRaises(ApprovalError):
            _ = consent2_approval(subject="")


if __name__ == "__main__":
    unittest.main()
