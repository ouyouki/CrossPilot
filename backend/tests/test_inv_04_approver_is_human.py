"""INV-4: an approver is always a natural person; exactly one decider is set."""

from __future__ import annotations

import unittest

from crosspilot.approvals.model import ApprovalError
from crosspilot.approvals.service import ApprovalDecision
from crosspilot.approvals.state_machine import ApprovalStatus
from crosspilot.core.errors import ToolGateError

from .support import PILOT, consent2_approval, harness


class Inv04ApproverIsHuman(unittest.TestCase):
    def test_agent_cannot_decide(self):
        h = harness()
        pending = h.service.submit(h.service.create(consent2_approval()).id, now=h.clock.now())

        with self.assertRaises(ToolGateError) as ctx:
            h.service.decide(
                pending.id,
                actor=PILOT,
                if_match_version=pending.version,
                payload_hash=pending.payload_hash,
                decision=ApprovalDecision.APPROVE,
            )

        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")
        self.assertEqual(h.repo.get(pending.id).status, ApprovalStatus.PENDING)

    def test_approver_kind_must_be_human(self):
        h = harness()
        pending = h.service.submit(h.service.create(consent2_approval()).id, now=h.clock.now())

        with self.assertRaises(ApprovalError):
            pending.transition(
                ApprovalStatus.APPROVED,
                now=h.clock.now(),
                approver_user_id="agent:pilot",
                approver_kind="agent",
            )

    def test_exactly_one_decider(self):
        h = harness()
        pending = h.service.submit(h.service.create(consent2_approval()).id, now=h.clock.now())

        with self.assertRaises(ApprovalError):
            pending.transition(
                ApprovalStatus.APPROVED,
                now=h.clock.now(),
                approver_user_id="u-operator",
                approver_kind="human",
                delegated_via_grant_id="g-1",
            )

        with self.assertRaises(ApprovalError):
            pending.transition(ApprovalStatus.APPROVED, now=h.clock.now())

    def test_grant_delegation_records_the_grant_not_a_person(self):
        h = harness()
        pending = h.service.submit(h.service.create(consent2_approval()).id, now=h.clock.now())

        delegated = pending.transition(
            ApprovalStatus.APPROVED,
            now=h.clock.now(),
            delegated_via_grant_id="g-1",
        )

        self.assertIsNone(delegated.approver_user_id)
        self.assertEqual(delegated.delegated_via_grant_id, "g-1")


if __name__ == "__main__":
    unittest.main()
