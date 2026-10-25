"""#8 最小可跑骨架的自动用例(TC-8-01〜06、09)。

测试只打两个接缝:处理器返回的结构,以及成本数字与 `costing.compute` 的一致性。
"""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from app import handlers, server
from crosspilot.costing import compute


def _sample(name: str) -> dict:
    return json.loads((handlers.SAMPLE_DIR / name).read_text(encoding="utf-8"))


class SkeletonApi(unittest.TestCase):
    def test_TC_8_01_health(self):
        # TC-8-01: /healthz 返回 ok
        self.assertEqual(handlers.health(), {"status": "ok"})

    def test_TC_8_02_today_has_three_blocks(self):
        # TC-8-02: 今日页三块都在
        payload = handlers.today()
        self.assertIn("pending_approvals", payload)
        self.assertIn("readiness", payload)
        self.assertIn("missing", payload["readiness"])
        self.assertIsInstance(payload["reminders"], list)

    def test_TC_8_03_candidates_rows(self):
        # TC-8-03: 每行有 id/title/price/margin/status
        payload = handlers.candidates()
        self.assertGreaterEqual(len(payload["items"]), 3)
        for row in payload["items"]:
            for key in ("id", "title", "price_jpy", "margin", "status", "cost_items"):
                self.assertIn(key, row)
            if row["status"] == "COMPUTED":
                self.assertEqual(len(row["cost_items"]), 16)
            else:
                # 算不出来的候选不产出金额,只说明缺什么(INV-10)
                self.assertEqual(row["cost_items"], [])
                self.assertTrue(row["missing"])

    def test_TC_8_04_cost_items_match_costing(self):
        # TC-8-04: 页面上的 16 项与 costing.compute 的输出逐项一致
        raw = _sample("candidates.json")["items"][0]
        expected = compute(handlers._to_input(raw))
        row = handlers.candidates()["items"][0]
        got = {item["key"]: item["value_jpy"] for item in row["cost_items"]}
        want = {item.key: item.value_jpy for item in expected.items}
        self.assertEqual(got, want)
        self.assertEqual(row["profit"], expected.profit)
        # 16 项之和 + 利润 = 营收(没有第二套算法)
        self.assertEqual(sum(got.values()) + row["profit"], row["revenue"])

    def test_TC_8_05_one_broken_candidate_does_not_break_others(self):
        # TC-8-05: 某条候选缺 BLOCKING 项 → 该行 UNKNOWN,其他行照常
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            data = _sample("candidates.json")
            del data["items"][0]["rate_card"]["c3_intl_ship"]
            (folder / "candidates.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            payload = handlers.candidates(sample_dir=folder)

        broken, fine = payload["items"][0], payload["items"][1]
        self.assertEqual(broken["status"], "UNKNOWN")
        self.assertIn("c3_intl_ship", broken["missing"])
        self.assertIsNone(broken["margin"])
        self.assertEqual(fine["status"], "COMPUTED")

    def test_TC_8_06_missing_sample_file_returns_empty_state(self):
        # TC-8-06: 样例文件缺失 → 空列表 + 说明,不抛异常
        with tempfile.TemporaryDirectory() as tmp:
            payload = handlers.candidates(sample_dir=Path(tmp))
        self.assertEqual(payload["items"], [])
        self.assertTrue(payload["notes"])

    def test_TC_8_09_starts_and_serves_without_network(self):
        # TC-8-09: 只用标准库启动,本机请求 /healthz 能通(不访问外网)
        httpd = server.make_server("127.0.0.1", 0)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            port = httpd.server_address[1]
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=5) as resp:
                self.assertEqual(json.loads(resp.read())["status"], "ok")
        finally:
            httpd.shutdown()
            httpd.server_close()


class SkeletonSampleShape(unittest.TestCase):
    def test_sample_candidates_cover_all_tax_regimes_used(self):
        # 样例要能演示「可算」和「不可算」两种状态
        rows = handlers.candidates()["items"]
        statuses = {row["status"] for row in rows}
        self.assertIn("COMPUTED", statuses)
        self.assertIn("UNKNOWN", statuses)


if __name__ == "__main__":
    unittest.main()
