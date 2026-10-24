"""INV-11: every call is audited — including refusals — in an append-only,
hash-chained log that detects tampering."""

from __future__ import annotations

import unittest
from dataclasses import replace

from crosspilot.audit.log import AuditDecision, AuditLog, GENESIS
from crosspilot.core.errors import ToolGateError

from .support import NOW, consent2_approval, execution_call, harness


class Inv11AuditChain(unittest.TestCase):
    def _log(self, count: int = 3) -> AuditLog:
        log = AuditLog()
        for index in range(count):
            log.append(
                ts=NOW,
                actor_type="agent",
                actor_id="agent:Scout",
                action="ACT-SCORE",
                target=f"cand-{index}",
                decision=AuditDecision.ALLOWED,
                details={"index": index},
            )
        return log

    def test_chain_is_linked_and_valid(self):
        log = self._log()
        entries = log.entries()
        self.assertEqual(entries[0].prev_hash, GENESIS)
        for previous, current in zip(entries, entries[1:]):
            self.assertEqual(current.prev_hash, previous.hash)
        self.assertTrue(log.verify().ok)
        self.assertEqual(log.checkpoint()["last_hash"], entries[-1].hash)

    def test_tampering_breaks_the_chain(self):
        log = self._log()
        log._entries[1] = replace(log._entries[1], details={"index": 99})  # noqa: SLF001
        result = log.verify()
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_at, 2)

    def test_refused_calls_are_audited(self):
        h = harness()
        executed: list[object] = []

        with self.assertRaises(ToolGateError):
            h.gate.call(execution_call(approval_id=None), executed.append)

        entries = h.audit.entries()
        self.assertEqual(len(entries), 1)
        self.assertIs(entries[0].decision, AuditDecision.DENIED)
        self.assertEqual(entries[0].actor_id, "agent:Lister")
        self.assertTrue(h.audit.verify().ok)

    def test_allowed_execution_is_audited_with_approval(self):
        h = harness()
        h.approve(h.service.create(consent2_approval()))
        h.gate.call(execution_call(approval_id="ap-1"), lambda approval: None)

        entry = h.audit.entries()[-1]
        self.assertIs(entry.decision, AuditDecision.ALLOWED)
        self.assertEqual(entry.details["approval_id"], "ap-1")

    def test_log_has_no_mutation_api(self):
        log = AuditLog()
        for forbidden in ("update", "delete", "remove", "update_entry", "delete_entry"):
            self.assertFalse(hasattr(log, forbidden), f"audit exposes {forbidden}")


if __name__ == "__main__":
    unittest.main()
