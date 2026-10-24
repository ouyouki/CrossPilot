"""INV-18: an approval is immutable once PENDING, and a decision must quote the
exact version and payload hash the person saw."""

from __future__ import annotations

import unittest

from crosspilot.approvals.model import ApprovalError
from crosspilot.approvals.service import ApprovalDecision
from crosspilot.approvals.state_machine import ApprovalStatus
from crosspilot.core.errors import ToolGateError

from .support import OPERATOR, consent2_approval, harness


class Inv18ApprovalImmutable(unittest.TestCase):
    def _pending(self, *, required_viewed: tuple[str, ...] = ()):
        h = harness()
        approval = h.service.create(consent2_approval(required_viewed=required_viewed))
        return h, h.service.submit(approval.id, now=h.clock.now())

    def test_stale_version_is_rejected(self):
        h, pending = self._pending()
        with self.assertRaises(ToolGateError) as ctx:
            h.service.decide(
                pending.id,
                actor=OPERATOR,
                if_match_version=pending.version - 1,
                payload_hash=pending.payload_hash,
                decision=ApprovalDecision.APPROVE,
            )
        self.assertEqual(ctx.exception.code, "VERSION_CONFLICT")
        self.assertEqual(h.repo.get(pending.id).status, ApprovalStatus.PENDING)

    def test_wrong_payload_hash_is_rejected(self):
        h, pending = self._pending()
        with self.assertRaises(ToolGateError) as ctx:
            h.service.decide(
                pending.id,
                actor=OPERATOR,
                if_match_version=pending.version,
                payload_hash="b" * 64,
                decision=ApprovalDecision.APPROVE,
            )
        self.assertEqual(ctx.exception.code, "VERSION_CONFLICT")

    def test_required_evidence_must_be_viewed(self):
        h, pending = self._pending(required_viewed=("compliance_report", "asset_side_by_side"))
        with self.assertRaises(ToolGateError) as ctx:
            h.service.decide(
                pending.id,
                actor=OPERATOR,
                if_match_version=pending.version,
                payload_hash=pending.payload_hash,
                decision=ApprovalDecision.APPROVE,
            )
        self.assertEqual(ctx.exception.code, "EVIDENCE_NOT_VIEWED")
        self.assertIn("compliance_report", ctx.exception.extra["missing_sections"])

        h.service.record_view(pending.id, user_id=OPERATOR.id, section="compliance_report")
        h.service.record_view(pending.id, user_id=OPERATOR.id, section="asset_side_by_side")
        decided = h.service.decide(
            pending.id,
            actor=OPERATOR,
            if_match_version=pending.version,
            payload_hash=pending.payload_hash,
            decision=ApprovalDecision.APPROVE,
        )
        self.assertEqual(decided.status, ApprovalStatus.APPROVED)

    def test_content_cannot_change_after_pending(self):
        h, pending = self._pending()
        with self.assertRaises(ApprovalError):
            pending.transition(
                ApprovalStatus.APPROVED,
                now=h.clock.now(),
                approver_user_id=OPERATOR.id,
                approver_kind="human",
                what_changes={"title": "different product"},
            )

    def test_a_decision_cannot_be_repeated(self):
        h, pending = self._pending()
        h.service.decide(
            pending.id,
            actor=OPERATOR,
            if_match_version=pending.version,
            payload_hash=pending.payload_hash,
            decision=ApprovalDecision.APPROVE,
        )
        with self.assertRaises(ToolGateError) as ctx:
            h.service.decide(
                pending.id,
                actor=OPERATOR,
                if_match_version=pending.version + 1,
                payload_hash=pending.payload_hash,
                decision=ApprovalDecision.APPROVE,
            )
        self.assertEqual(ctx.exception.code, "NOT_APPROVED")


if __name__ == "__main__":
    unittest.main()
