"""#24:审批中心的自动用例(TC-24-01〜08)。"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from app import approvals_api, handlers, selection, server, store
from crosspilot.core.errors import ToolGateError


def reset() -> None:
    from crosspilot.approvals.repo import InMemoryApprovalRepo
    from crosspilot.approvals.service import ApprovalsService

    store.repo = InMemoryApprovalRepo()
    store.service = ApprovalsService(store.repo, store.clock)


def make_selection() -> tuple[str, dict]:
    ids = [row["id"] for row in handlers.candidates()["items"]][:2]
    result = selection.create_selection(ids)
    return result["approval_id"], result


class ApprovalDetail(unittest.TestCase):
    def setUp(self) -> None:
        reset()
        self.approval_id, _ = make_selection()

    def test_TC_24_01_detail_has_subjects_and_evidence(self):
        # TC-24-01: 详情带对象、必看分区与证据
        payload = approvals_api.detail(self.approval_id)
        self.assertEqual(payload["status"], "PENDING")
        self.assertEqual(len(payload["subject_refs"]), 2)
        self.assertEqual(len(payload["evidence"]), 2)
        self.assertTrue(payload["required_viewed"])
        self.assertEqual(payload["evidence"][0]["status"], "COMPUTED")
        self.assertEqual(len(payload["evidence"][0]["cost_items"]), 16)

    def test_TC_24_09_record_view_tracks_section(self):
        # TC-24-09: 记录已查看后,viewed 增加
        before = approvals_api.detail(self.approval_id)["viewed"]
        self.assertNotIn("cost_breakdown", before)
        approvals_api.record_view(self.approval_id, "cost_breakdown")
        after = approvals_api.detail(self.approval_id)["viewed"]
        self.assertIn("cost_breakdown", after)

    def test_TC_24_02_unknown_id(self):
        # TC-24-02: 不存在的单
        with self.assertRaises(approvals_api.ApprovalNotFound):
            approvals_api.detail("ap-nope")


class ApprovalDecide(unittest.TestCase):
    def setUp(self) -> None:
        reset()
        self.approval_id, _ = make_selection()
        self.detail = approvals_api.detail(self.approval_id)

    def _body(self, decision: str = "APPROVE", **over):
        body = {
            "decision": decision,
            "version": self.detail["version"],
            "payload_hash": self.detail["payload_hash"],
        }
        body.update(over)
        return body

    def test_TC_24_03_cannot_approve_before_viewing(self):
        # TC-24-03: 必看证据没看 → 409 EVIDENCE_NOT_VIEWED
        with self.assertRaises(ToolGateError) as ctx:
            approvals_api.decide(self.approval_id, self._body())
        self.assertEqual(ctx.exception.code, "EVIDENCE_NOT_VIEWED")
        self.assertEqual(approvals_api.detail(self.approval_id)["status"], "PENDING")

    def test_TC_24_04_approve_after_viewing(self):
        # TC-24-04: 看过必看分区 → APPROVED,不再出现在待批
        for section in self.detail["required_viewed"]:
            approvals_api.record_view(self.approval_id, section)
        result = approvals_api.decide(self.approval_id, self._body())
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["approver_kind"], "human")
        self.assertEqual(selection.approvals()["count"], 0)

    def test_TC_24_05_wrong_version_conflicts(self):
        # TC-24-05: 版本不符 → 412 VERSION_CONFLICT
        for section in self.detail["required_viewed"]:
            approvals_api.record_view(self.approval_id, section)
        with self.assertRaises(ToolGateError) as ctx:
            approvals_api.decide(self.approval_id, self._body(version=self.detail["version"] - 1))
        self.assertEqual(ctx.exception.code, "VERSION_CONFLICT")
        self.assertEqual(ctx.exception.http_status, 412)

    def test_TC_24_06_return_needs_reason(self):
        # TC-24-06: 退回必须带预定义原因
        for section in self.detail["required_viewed"]:
            approvals_api.record_view(self.approval_id, section)
        with self.assertRaises(ToolGateError) as ctx:
            approvals_api.decide(self.approval_id, self._body("RETURN"))
        self.assertEqual(ctx.exception.code, "ACTION_FORBIDDEN")
        result = approvals_api.decide(
            self.approval_id, self._body("RETURN", return_reason_code="WARRING" if False else "WORDING")
        )
        self.assertEqual(result["status"], "RETURNED")

    def test_TC_24_07_reject(self):
        # TC-24-07: 拒绝 → REJECTED
        for section in self.detail["required_viewed"]:
            approvals_api.record_view(self.approval_id, section)
        result = approvals_api.decide(self.approval_id, self._body("REJECT"))
        self.assertEqual(result["status"], "REJECTED")


class ApprovalHttp(unittest.TestCase):
    def setUp(self) -> None:
        reset()
        self.approval_id, _ = make_selection()
        self.httpd = server.make_server("127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_TC_24_08_http_detail_and_decide(self):
        # TC-24-08: HTTP 层:详情 200;未看证据批准 → 409 + problem+json
        status, body = self.request("GET", f"/api/v1/approvals/{self.approval_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "PENDING")

        status, body = self.request(
            "POST",
            f"/api/v1/approvals/{self.approval_id}/decide",
            {"decision": "APPROVE", "version": body["version"], "payload_hash": body["payload_hash"]},
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "EVIDENCE_NOT_VIEWED")

        for section in ("cost_breakdown", "g0_verdict", "demand_signal"):
            self.request("POST", f"/api/v1/approvals/{self.approval_id}/views", {"section": section})

        detail = self.request("GET", f"/api/v1/approvals/{self.approval_id}")[1]
        status, body = self.request(
            "POST",
            f"/api/v1/approvals/{self.approval_id}/decide",
            {"decision": "APPROVE", "version": detail["version"], "payload_hash": detail["payload_hash"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "APPROVED")


if __name__ == "__main__":
    unittest.main()
