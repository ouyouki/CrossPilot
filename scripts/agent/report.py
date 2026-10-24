"""Agent 运行的看板(docs/运营规则.md 5.1):把 tmp/agent-logs/runs.jsonl 做成一个本地 HTML,用来调整 [runner] 的上限。

    python scripts/agent/report.py [--days 14] [--out tmp/agent-report.html]

看什么:每天各环境的次数和 Token(对上限的比例)、超时和失败、读不到用量的次数;每件事(Issue)的累计 Token 和阻塞;
各命令的平均 Token 和用时、重试;最近的阻塞和跳过。只读本地文件,不联网;生成的文件在 tmp/ 下(不进 git),用浏览器打开。
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import tomllib
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path, since: str) -> list[dict]:
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(r, dict) and str(r.get("time", ""))[:10] >= since:
                rows.append(r)
    return rows


def bar(value: float, cap: float) -> str:
    pct = 0 if not cap else min(100, round(value * 100 / cap))
    cls = "hi" if pct >= 100 else "warn" if pct >= 80 else ""
    return f'<span class="bar {cls}"><i style="width:{pct}%"></i></span> {pct}%'


def table(head: list[str], rows: list[list[str]], empty: str = "没有记录") -> str:
    if not rows:
        return f"<p class=muted>{empty}</p>"
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{tr}</table>"


def render(rows: list[dict], rc: dict, days: int) -> str:
    e = html.escape
    runs = [r for r in rows if r.get("event") == "run"]
    caps_t, caps_r = rc.get("daily_tokens", {}), rc.get("max_runs_per_day", {})        # 没写时的默认值和 run.py 一样

    daily = defaultdict(lambda: {"runs": 0, "tokens": 0, "timeout": 0, "fail": 0, "unknown": 0, "block": 0})
    for r in rows:
        d = daily[(r["time"][:10], r.get("side", "?"))]
        if r.get("event") == "run":
            d["runs"] += 1
            d["tokens"] += int(r.get("tokens", 0))
            d["timeout"] += r.get("code") == "超时"
            d["fail"] += r.get("code") not in ("0", "超时")
            d["unknown"] += not r.get("known", True)
        elif r.get("event") == "block":
            d["block"] += 1
    t_daily = [[e(day), e(side), str(d["runs"]), bar(d["runs"], caps_r.get(side, 60)), f"{d['tokens']:,}", bar(d["tokens"], caps_t.get(side, 10_000_000)),
                str(d["timeout"]), str(d["fail"]), str(d["unknown"]), str(d["block"])]
               for (day, side), d in sorted(daily.items(), reverse=True)]

    issues = defaultdict(lambda: {"tokens": 0, "runs": 0, "block": 0, "last": ""})
    for r in rows:
        if not r.get("issue"):
            continue
        i = issues[int(r["issue"])]
        if r.get("event") == "run":
            i["tokens"] += int(r.get("tokens", 0))
            i["runs"] += 1
            i["last"] = r.get("command", "")
        elif r.get("event") == "block":
            i["block"] += 1
    cap_i = rc.get("issue_tokens", 5_000_000)
    t_issue = [[f"#{n}", f"{i['tokens']:,}", bar(i["tokens"], cap_i), str(i["runs"]), str(i["block"]), e(i["last"])]
               for n, i in sorted(issues.items(), key=lambda x: -x[1]["tokens"])[:30]]

    cmds = defaultdict(lambda: {"runs": 0, "tokens": 0, "seconds": 0, "retry": 0})
    for r in runs:
        c = cmds[(r.get("side", "?"), str(r.get("command", "")).split()[0])]
        c["runs"] += 1
        c["tokens"] += int(r.get("tokens", 0))
        c["seconds"] += int(r.get("seconds", 0))
        c["retry"] += int(r.get("tries", 1)) > 1
    t_cmd = [[e(side), e(name), str(c["runs"]), f"{c['tokens'] // c['runs']:,}", f"{c['seconds'] // c['runs'] // 60} 分",
              str(c["retry"])] for (side, name), c in sorted(cmds.items(), key=lambda x: -x[1]["tokens"])]

    t_evt = [[e(r["time"][:16].replace("T", " ")), e(r.get("side", "")), "阻塞" if r["event"] == "block" else "跳过",
              f"#{r['issue']}" if r.get("issue") else "-", e(r.get("command", "")), e(r.get("why", ""))]
             for r in sorted((r for r in rows if r.get("event") in ("block", "skip")), key=lambda r: r["time"], reverse=True)[:30]]

    total = sum(int(r.get("tokens", 0)) for r in runs)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent 运行看板</title>
<style>
:root {{ --bg:#fff; --fg:#1f2328; --muted:#656d76; --line:#d0d7de; --bar:#0969da; --warn:#bf8700; --hi:#cf222e; --track:#eaeef2; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0d1117; --fg:#e6edf3; --muted:#8d96a0; --line:#30363d; --bar:#4493f8; --warn:#d29922; --hi:#f85149; --track:#21262d; }} }}
body {{ background:var(--bg); color:var(--fg); font:14px/1.5 system-ui,sans-serif; margin:0 auto; padding:16px; max-width:1100px; }}
h1 {{ font-size:20px; }} h2 {{ font-size:16px; margin-top:28px; }} .muted {{ color:var(--muted); }}
.wrap {{ overflow-x:auto; }} table {{ border-collapse:collapse; width:100%; }}
th, td {{ border-bottom:1px solid var(--line); padding:4px 8px; text-align:left; white-space:nowrap; }}
.bar {{ display:inline-block; width:80px; height:8px; background:var(--track); border-radius:4px; vertical-align:middle; }}
.bar i {{ display:block; height:100%; background:var(--bar); border-radius:4px; }}
.bar.warn i {{ background:var(--warn); }} .bar.hi i {{ background:var(--hi); }}
</style></head><body>
<h1>Agent 运行看板</h1>
<p class=muted>最近 {days} 天 · 运行 {len(runs)} 次 · 等价 Token {total:,} · 生成于 {e(datetime.now().strftime('%Y-%m-%d %H:%M'))} ·
上限见 project.toml 的 [runner](80% 黄色,100% 红色)</p>
<h2>每天</h2><div class=wrap>{table(["日期", "环境", "次数", "次数/上限", "Token", "Token/上限", "超时", "失败", "读不到用量", "阻塞"], t_daily)}</div>
<h2>每件事(Token 最多的 30 件)</h2><div class=wrap>{table(["Issue", "Token", "对 issue_tokens", "次数", "阻塞", "最后的命令"], t_issue)}</div>
<h2>各命令</h2><div class=wrap>{table(["环境", "命令", "次数", "平均 Token", "平均用时", "重试过"], t_cmd)}</div>
<h2>最近的阻塞和跳过</h2><div class=wrap>{table(["时间", "环境", "事件", "Issue", "命令", "理由"], t_evt, "没有阻塞和跳过")}</div>
</body></html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Agent 运行的看板")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--out", default="tmp/agent-report.html")
    ap.add_argument("--log", default="tmp/agent-logs/runs.jsonl")
    args = ap.parse_args(argv)
    rc = tomllib.loads((ROOT / "project.toml").read_text(encoding="utf-8")).get("runner", {})
    since = (datetime.now() - timedelta(days=args.days - 1)).strftime("%Y-%m-%d")
    rows = load(ROOT / args.log, since)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, rc, args.days), encoding="utf-8")
    print(f"report: {len(rows)} 条记录 → {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
