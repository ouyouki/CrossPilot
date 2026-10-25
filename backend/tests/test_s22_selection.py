"""#22:候选页可用化 + 同意 1 的自动用例(TC-22-01〜05)。"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request

from app import handlers, selection, server, store


def reset() -> None:
    """每个用例从干净的内存状态开始。"""
    from crosspilot.approvals.repo import InMemoryApprovalRepo
    from crosspilot.approvals.service import ApprovalsService

    store.repo = InMemoryApprovalRepo()
    store.service = ApprovalsService(store.repo, store.clock)


class SelectionApi(unittest.TestCase):
    def setUp(self) -> None:
        reset()

    def test_TC_22_01_empty_list_initially(self):
        # TC-22-01: 一开始没有待批单
        payload = selection.approvals()
        self.assertEqual(payload["items"], [])
        self.assertEqual(payload["persistence"], "memory")

    def test_TC_22_02_creates_pending_approval(self):
        # TC-22-02: 勾选 2 个 → 生成 PENDING 的 ACT-SELECT 单
        ids = [row["id"] for row in handlers.candidates()["items"]][:2]
        result = selection.create_selection(ids)
        self.assertEqual(result["status"], "PENDING")
        self.assertFalse(result["duplicate"])
        listed = selection.approvals()["items"]
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["subject_refs"], ids)

    def test_TC_22_03_over_cap_is_rejected(self):
        # TC-22-03: 超过单批上限被拒绝,并说明原因
        ids = [f"cand-{i}" for i in range(store.SELECTION_CAP + 1)]
        with self.assertRaises(selection.SelectionError) as ctx:
            selection.create_selection(ids)
        self.assertEqual(ctx.exception.code, "OVER_CAP")

    def test_TC_22_04_unknown_subject_is_rejected(self):
        # TC-22-04: 候选不存在时拒绝,不建单
        with self.assertRaises(selection.SelectionError) as ctx:
            selection.create_selection(["cand-does-not-exist"])
        self.assertEqual(ctx.exception.code, "UNKNOWN_SUBJECT")
        self.assertEqual(selection.approvals()["items"], [])

    def test_TC_22_05_same_batch_is_idempotent(self):
        # TC-22-05: 同一批重复提交不重复建单
        ids = [row["id"] for row in handlers.candidates()["items"]][:2]
        first = selection.create_selection(ids)
        second = selection.create_selection(ids)
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["approval_id"], second["approval_id"])
        self.assertEqual(len(selection.approvals()["items"]), 1)


class SelectionHttp(unittest.TestCase):
    def setUp(self) -> None:
        reset()
        self.httpd = server.make_server("127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def post(self, payload: dict) -> tuple[int, dict]:
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/v1/approvals/selection",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_TC_22_06_http_created_and_problem_json(self):
        # TC-22-06: HTTP 层:成功 201;超上限 422 + problem+json
        ids = [row["id"] for row in handlers.candidates()["items"]][:1]
        status, body = self.post({"subject_refs": ids})
        self.assertEqual(status, 201)
        self.assertEqual(body["status"], "PENDING")

        status, body = self.post({"subject_refs": [f"cand-{i}" for i in range(99)]})
        self.assertEqual(status, 422)
        self.assertEqual(body["code"], "OVER_CAP")

    def test_TC_22_07_http_duplicate_returns_200(self):
        # TC-22-07: 重复提交返回 200 且 duplicate=true
        ids = [row["id"] for row in handlers.candidates()["items"]][:1]
        self.post({"subject_refs": ids})
        status, body = self.post({"subject_refs": ids})
        self.assertEqual(status, 200)
        self.assertTrue(body["duplicate"])


if __name__ == "__main__":
    unittest.main()
