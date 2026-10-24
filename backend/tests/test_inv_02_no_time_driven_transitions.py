"""INV-2: no clock-driven approval transition exists.

Two independent checks:

* the transition table has no time edge (structural), and
* a PENDING approval is still PENDING after a simulated year, and can still be
  decided — approvals do not expire (RL-1).
"""

from __future__ import annotations

import unittest
from datetime import timedelta

from crosspilot.approvals.state_machine import (
    ApprovalStatus,
    TRANSITIONS,
    assert_no_time_driven_edges,
)

from .support import OPERATOR, consent2_approval, harness


class Inv02NoTimeDrivenTransitions(unittest.TestCase):
    def test_transition_table_is_time_free(self):
        assert_no_time_driven_edges()
        # No status transition is triggered by anything but an explicit call:
        # there is no "expired" or "timed_out" status at all.
        names = {status.value for status in ApprovalStatus}
        self.assertNotIn("EXPIRED", names)
        self.assertNotIn("TIMED_OUT", names)
        self.assertEqual(TRANSITIONS[ApprovalStatus.OUTCOME_UNKNOWN], frozenset())

    def test_pending_survives_a_year(self):
        h = harness()
        approval = h.service.create(consent2_approval())
        pending = h.service.submit(approval.id, now=h.clock.now())

        h.clock.advance(timedelta(days=365))

        still_pending = h.repo.get(pending.id)
        self.assertEqual(still_pending.status, ApprovalStatus.PENDING)
        self.assertEqual(still_pending.pending_since, pending.pending_since)

    def test_decidable_after_a_year(self):
        from crosspilot.approvals.service import ApprovalDecision

        h = harness()
        approval = h.service.create(consent2_approval())
        pending = h.service.submit(approval.id, now=h.clock.now())
        h.clock.advance(timedelta(days=365))

        decided = h.service.decide(
            pending.id,
            actor=OPERATOR,
            if_match_version=pending.version,
            payload_hash=pending.payload_hash,
            decision=ApprovalDecision.APPROVE,
            now=h.clock.now(),
        )

        self.assertEqual(decided.status, ApprovalStatus.APPROVED)


if __name__ == "__main__":
    unittest.main()
