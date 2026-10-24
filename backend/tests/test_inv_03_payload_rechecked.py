"""INV-3: the payload hash is recomputed at execution; a mismatch voids the
approval, opens a successor with a diff, and executes nothing."""

from __future__ import annotations

import unittest

from crosspilot.approvals.preconditions import FactSnapshot
from crosspilot.core.errors import ToolGateError

from .support import PayloadGuard, consent2_approval, execution_call, harness


class Inv03PayloadRecheckedAtExecution(unittest.TestCase):
    def test_changed_payload_is_voided_and_succeeded(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        guard = PayloadGuard(h.service, FactSnapshot(payload_hash="b" * 64))
        h.with_guard(guard)
        executed: list[object] = []

        with self.assertRaises(ToolGateError) as ctx:
            h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(ctx.exception.code, "PRECONDITION_FAILED")
        self.assertIn("successor_id", ctx.exception.extra)
        self.assertEqual(executed, [], "nothing may be executed after a hash mismatch")

        old = h.repo.get("ap-1")
        self.assertEqual(old.status.value, "VOID")
        self.assertTrue(old.void_reasons)

        successor = h.repo.get(old.successor_id)
        self.assertEqual(successor.status.value, "PENDING")
        self.assertEqual(successor.subject_refs, old.subject_refs)
        self.assertEqual(successor.payload_hash, "b" * 64)
        diff = successor.what_changes["diff_vs_previous_approval"]
        self.assertEqual(diff[0]["pc"], "PC-PAYLOAD")

    def test_unchanged_payload_executes(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        guard = PayloadGuard(h.service, FactSnapshot(payload_hash="a" * 64))
        h.with_guard(guard)
        executed: list[object] = []

        h.gate.call(execution_call(approval_id="ap-1"), executed.append)

        self.assertEqual(len(executed), 1)
        self.assertEqual(h.repo.get("ap-1").status.value, "EXECUTED")


if __name__ == "__main__":
    unittest.main()
