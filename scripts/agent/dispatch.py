"""调度:读 GitHub 上的状态,决定这个环境下一步让哪个 Agent 做什么(docs/运营规则.md 5 章)。确定性的程序,不是 LLM。

    python scripts/agent/dispatch.py next --side <dev|pm|review> [--state <JSON>]
    python scripts/agent/dispatch.py state --side <dev|pm|review>          # 只把读到的状态显示出来(排查用)

输出一行 JSON:{"agent", "command", "key", "issue"};没有可做的事时 {"command": null, "reason": …}。
--state 用 JSON 文件代替 GitHub(测试用);省略时经 bash scripts/github/bot.sh <side> 读 GitHub。

每个环境的优先顺序(从上往下,第一个满足的):
  pm      1 /answer <N>       Issue 带 待回答
          2 /pm-accept <PR>   评审 App 批准了当前提交、测试通过、PM 还没有结论
          3 /pickup <N>       状态:待处理;或方案被 D1 退回(在最后一次方案的 [进度] 之后)
  review  1 /review <N> 方案       方案的 [进度] 在最后一次 D1 结论之后
          2 /review <N> 测试用例   测试用例的 [进度] 在最后一次 D2 结论之后
          3 /review <PR>      当前提交还没有评审 App 的正式评审(CI 失败的不评审)
          4 /test <PR>        评审 App 批准了当前提交,还没有测试的结论
          5 /architecture     「每日计划」里评审 App 上次的 [架构建议] 已过 [cycle] weekly_days 天
  dev     1 /merge <PR>       批准、测试通过、PM 通过都针对当前提交,CI 全部成功(main 的 full-test 失败时只合并撤回 PR)
          2 /revert <PR>      人在已合并的 PR 上写了 [退回],还没有撤回 PR
          3 /integrate main   main 上的 full-test 失败,还没有开着的撤回 PR,也还没为这个提交写过 [阻塞](找原因,请人写 [退回])
          4 /dev <N>          PR 的当前提交被要求修改、测试或 PM 退回、CI 失败,或三方都通过而 gate 失败
                              (Issue 已关闭、等人、撤回 PR、已请重新做 D2 时不派)
          5 /wrapup           有 状态:待验收 的 Issue,它的 PR 已在最新的 Release 里
          6 /integrate        到了 integrate_at,「每日计划」里还没有今天的 [验收清单]
          7 /dev <N>          已定版(人或自动),没有开着的或已合并(且没被撤回)的 PR,不在等 D2、回答、人的决定,
                              `依赖:` 的 Issue 都已关闭或已合并
          8 /retro            「每日计划」里开发 App 上次的 [回顾] 已过 [cycle] weekly_days 天
都跳过:带 阻塞 的 Issue 和它的 PR;待回答 的 Issue、待人决定 而人还没写 [决定] 的 Issue 不开发。
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print("dispatch: 需要 Python 3.11 以上", file=sys.stderr)
    sys.exit(2)

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "github"))
from gates import (Config, UsageError, approval, design_status, first_line, head_verdict,  # noqa: E402
                   last_verdict, parse_time, unedited)

AGENT = {"pickup": "pm", "answer": "pm", "pm-accept": "pm", "review": "reviewer", "test": "tester", "dev": "developer",
         "merge": "integrator", "integrate": "integrator", "revert": "integrator", "wrapup": "integrator",
         "architecture": "reviewer", "retro": "integrator"}
REQUIRED = ("tests", "secrets", "scope", "trace")


def progress_after(comments: list[dict], stage: str, verdict: dict | None) -> bool:
    """`[进度] … <stage> 完成` 在最后一次结论之后。"""
    last = None
    for c in comments:
        if first_line(c["body"]).startswith("[进度]") and re.search(rf"{stage}\s*完成", first_line(c["body"])):
            last = c if last is None or c["created_at"] > last["created_at"] else last
    return last is not None and (verdict is None or last["created_at"] > verdict["created_at"])


def formal_on_head(reviews: list[dict], author: str, head: str) -> str:
    v = ""
    for r in sorted(reviews, key=lambda r: r["submitted_at"]):
        if r["author"] == author and r.get("commit_id") == head and r["state"] in ("APPROVED", "CHANGES_REQUESTED"):
            v = r["state"]
    return v


def weekly_due(cfg: Config, daily: dict | None, mark: str, author: str, now) -> bool:
    """「每日计划」里 author 最后一次写 mark 已经过了 [cycle] weekly_days 天(没写过也算)。"""
    if not daily:
        return False
    last = max((c["created_at"] for c in daily["comments"] if c["author"] == author and first_line(c["body"]).startswith(mark)),
               default="")
    return not last or (now - parse_time(last)).total_seconds() >= cfg.weekly_days * 86400


def open_deps(i: dict, issues: dict) -> list[int]:
    """正文 `依赖: #a, #b` 里写的 Issue 编号(调用方再看它们是否还开着)。"""
    m = re.search(r"^\W*依赖\s*[:：]\s*(.*)$", i.get("body") or "", re.M)
    return [int(n) for n in re.findall(r"#(\d+)", m.group(1))] if m else []


def issue_of(ref: str) -> int:
    m = re.match(r"^(?:feat|fix)/(\d+)-", ref or "")
    return int(m.group(1)) if m else 0


def fingerprint(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:12]


def task(command: str, issue: int, *parts) -> dict:
    name = command.split()[0].lstrip("/")
    return {"agent": AGENT[name], "command": command, "key": f"{command}@{fingerprint(*parts)}", "issue": issue}


def candidates(cfg: Config, st: dict, side: str):
    """按优先顺序列出这个环境可做的事。"""
    now = parse_time(st["now"])
    issues = {i["number"]: i for i in st["issues"] if i.get("state", "open") == "open" and "每日计划" not in i.get("title", "")}
    daily = next((i for i in st["issues"] if "每日计划" in i.get("title", "")), None)
    blocked = {n for n, i in issues.items() if "阻塞" in i["labels"]}
    prs = [p for p in st.get("prs", []) if issue_of(p["head_ref"]) not in blocked]
    rb, pb = cfg.review_bot, cfg.pm_bot

    def pr_state(p):
        h, rv = p["head_sha"], p["reviews"]
        return {"formal": formal_on_head(rv, rb, h), "appr": approval(rv, rb, h), "test": head_verdict(rv, rb, "测试", h),
                "pm": head_verdict(rv, pb, "PM", h), "checks": p.get("checks", ""), "gate": p.get("gate", "")}

    open_issues = [i for n, i in sorted(issues.items()) if n not in blocked]

    def waiting_human(i):
        """待回答,或 待人决定 而人还没在最后一条 [回答] 之后写 [决定]。"""
        if "待回答" in i["labels"]:
            return True
        if "待人决定" not in i["labels"]:
            return False
        answers = [c["created_at"] for c in i["comments"] if first_line(c["body"]).startswith("[回答]")]
        last = max(answers) if answers else ""
        return not any(cfg.is_human(c["author"]) and first_line(c["body"]).startswith("[决定]") and c["created_at"] > last
                       for c in i["comments"])
    if side == "pm":
        for i in open_issues:
            if "待回答" in i["labels"]:
                yield task(f"/answer {i['number']}", i["number"], i["labels"], len(i["comments"]))
        for p in prs:
            s = pr_state(p)
            if s["appr"] == "APPROVED" and s["test"] == "通过" and not s["pm"]:
                yield task(f"/pm-accept {p['number']}", issue_of(p["head_ref"]), p["head_sha"], len(p["reviews"]))
        for i in open_issues:
            d1 = last_verdict(i["comments"], rb, "方案")
            revise = (any(l in i["labels"] for l in ("状态:方案中", "状态:待定版")) and d1 is not None
                      and first_line(d1["body"]).startswith("[评审-退回]") and not progress_after(i["comments"], "方案", d1))
            if "状态:待处理" in i["labels"] or revise:
                yield task(f"/pickup {i['number']}", i["number"], i["labels"], len(i["comments"]))
        return

    if side == "review":
        for i in open_issues:
            if progress_after(i["comments"], "方案", last_verdict(i["comments"], rb, "方案")):
                yield task(f"/review {i['number']} 方案", i["number"], len(i["comments"]))
        for i in open_issues:
            if progress_after(i["comments"], "测试用例", last_verdict(i["comments"], rb, "测试用例")):
                yield task(f"/review {i['number']} 测试用例", i["number"], len(i["comments"]))
        for p in prs:
            s = pr_state(p)
            if not s["formal"] and s["checks"] != "failure":
                yield task(f"/review {p['number']}", issue_of(p["head_ref"]), p["head_sha"], len(p["reviews"]))
        for p in prs:
            s = pr_state(p)
            if s["formal"] == "APPROVED" and not s["test"]:
                yield task(f"/test {p['number']}", issue_of(p["head_ref"]), p["head_sha"], len(p["reviews"]))
        if weekly_due(cfg, daily, "[架构建议]", rb, now):
            yield task("/architecture", 0, now.astimezone(cfg.tz).strftime("%Y-%m-%d"))
        return

    # dev
    def all_passed(s):
        return s["appr"] == "APPROVED" and s["test"] == "通过" and s["pm"] == "通过"

    main_broken = st.get("main_full_test") == "failure"
    is_revert = lambda p: p["head_ref"].endswith("-revert")  # noqa: E731
    for p in sorted(prs, key=lambda p: not is_revert(p)):      # main 坏了时只合并撤回 PR
        s = pr_state(p)
        if all_passed(s) and s["checks"] == "success" and s["gate"] == "success" and (not main_broken or is_revert(p)):
            yield task(f"/merge {p['number']}", issue_of(p["head_ref"]), p["head_sha"])
    for r in st.get("rejected", []):
        if r.get("issue") not in blocked:
            yield task(f"/revert {r['pr']}", r.get("issue", 0), r)
    main_sha = st.get("main_sha", "")
    reported = daily and main_sha and any(c["author"] == cfg.dev_bot and first_line(c["body"]).startswith("[阻塞]")
                                         and main_sha[:7] in c["body"] for c in daily["comments"])
    if main_broken and not any(is_revert(p) for p in prs) and not reported:
        yield task("/integrate main", 0, main_sha)                 # 已经报告过这个提交时等人写 [退回]
    for p in prs:
        s = pr_state(p)
        i = issues.get(issue_of(p["head_ref"]))
        if i is None or waiting_human(i) or is_revert(p):
            continue                       # Issue 已关闭、等人、或撤回 PR(撤回 PR 不修改,退回时由人处理)
        if progress_after(i["comments"], "测试用例", last_verdict(i["comments"], rb, "测试用例")):
            continue                       # 已请重新做 D2,等评审
        if s["formal"] == "CHANGES_REQUESTED" or "退回" in (s["test"], s["pm"]) or s["checks"] == "failure" \
                or (all_passed(s) and s["gate"] == "failure"):
            yield task(f"/dev {issue_of(p['head_ref'])}", issue_of(p["head_ref"]), p["head_sha"], len(p["reviews"]),
                        s["checks"], s["gate"])
    rel = st.get("last_release") or {}
    if rel.get("published_at"):
        done = {m["issue"] for m in st.get("merged", []) if m.get("merged_at", "") < rel["published_at"]}
        if any("状态:待验收" in i["labels"] and i["number"] in done for i in open_issues):
            yield task("/wrapup", 0, rel["published_at"])
    local = now.astimezone(cfg.tz)
    today = local.strftime("%Y-%m-%d")
    if daily and (local.hour, local.minute) >= cfg.integrate_at:
        written = daily and any(first_line(c["body"]).startswith(f"[验收清单] {today}") for c in daily["comments"])
        if not written:
            yield task("/integrate", 0, today)
    live_merged = {m["issue"] for m in st.get("merged", []) if not m.get("reverted") and not m.get("is_revert")}
    with_pr = {issue_of(p["head_ref"]) for p in prs} | live_merged
    for i in open_issues:
        n, labels = i["number"], i["labels"]
        if n in with_pr or not any(l in labels for l in ("状态:待定版", "状态:开发中")):
            continue
        if waiting_human(i):
            continue
        if any(d in issues and d not in live_merged for d in open_deps(i, issues)):
            continue                                               # 依赖的 Issue 还没合并
        if not design_status(cfg, labels, i["comments"], now)[0]:
            continue
        if progress_after(i["comments"], "测试用例", last_verdict(i["comments"], rb, "测试用例")):
            continue                                               # waiting for D2
        yield task(f"/dev {n}", n, labels, len(i["comments"]))
    if weekly_due(cfg, daily, "[回顾]", cfg.dev_bot, now):
        yield task("/retro", 0, now.astimezone(cfg.tz).strftime("%Y-%m-%d"))
    return


def decide(cfg: Config, st: dict, side: str, skip: set[str] = frozenset()) -> dict:
    """第一件可做的事;skip 里的 key(今天已经放弃的事)跳过。"""
    for t in candidates(cfg, st, side):
        if t["key"] not in skip:
            return t
    return {"command": None, "reason": f"{ {'pm': 'PM', 'review': '评审和测试', 'dev': '开发'}[side] }没有可做的事"}


# ---------------------------------------------------------------------------------------------------------------------------------
# 从 GitHub 读状态(经 bot.sh,用这个环境的 App 身份)

def gather(cfg: Config, side: str) -> dict:
    bots = {cfg.dev_bot, cfg.pm_bot, cfg.review_bot}

    def gh(*args):
        r = subprocess.run(["bash", "scripts/github/bot.sh", side, "gh", *args], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise UsageError(f"gh {' '.join(args[:2])}: {r.stderr.strip()[:200]}")
        return json.loads(r.stdout or "null")

    def login(a):
        name = (a or {}).get("login", "")
        return name + "[bot]" if name + "[bot]" in bots else name

    def comments(cs):
        return [{"author": login(c.get("author")), "body": c.get("body") or "", "created_at": c["createdAt"],
                 "updated_at": "edited" if c.get("includesCreatedEdit") else c["createdAt"]} for c in cs or []]

    base = f"repos/{cfg.owner}/{cfg.repo}"
    issues = [{"number": i["number"], "title": i["title"], "state": "open", "labels": [l["name"] for l in i["labels"]],
               "body": i.get("body") or "", "comments": comments(i["comments"])}
              for i in gh("issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body,labels,comments")]
    prs = []
    for p in gh("pr", "list", "--state", "open", "--limit", "100",
                "--json", "number,headRefName,headRefOid,author,body,reviews,statusCheckRollup"):
        roll = {(c.get("name") or c.get("context")): (c.get("conclusion") or c.get("state") or c.get("status") or "").lower()
                for c in p.get("statusCheckRollup") or []}
        req = [roll.get(n, "") for n in REQUIRED]
        checks = "failure" if any(v in ("failure", "error", "cancelled", "timed_out") for v in req) else \
            "success" if all(v == "success" for v in req) else "pending"
        prs.append({"number": p["number"], "head_ref": p["headRefName"], "head_sha": p["headRefOid"], "author": login(p["author"]),
                    "body": p.get("body") or "", "checks": checks, "gate": roll.get("gate", ""),
                    "reviews": [{"author": login(r.get("author")), "state": r["state"], "body": r.get("body") or "",
                                 "submitted_at": r.get("submittedAt") or "", "commit_id": (r.get("commit") or {}).get("oid", "")}
                                for r in p.get("reviews") or []]})
    for i in issues:                    # 「每日计划」的评论多,gh issue list 只给前 100 条:改用分页的 API
        if "每日计划" in i["title"]:
            pages = gh("api", f"{base}/issues/{i['number']}/comments?per_page=100", "--paginate", "--slurp")
            i["comments"] = [{"author": login(c.get("user")), "body": c.get("body") or "", "created_at": c["created_at"],
                              "updated_at": c.get("updated_at") or c["created_at"]} for page in pages for c in page]
    st = {"now": datetime.now(timezone.utc).isoformat(), "issues": issues, "prs": prs}
    if side == "dev":
        merged = gh("pr", "list", "--state", "merged", "--limit", "100", "--json", "number,headRefName,body,mergedAt,comments")
        bodies = " ".join(p.get("body") or "" for p in merged + prs)
        reverted = {int(n) for m in merged if m["headRefName"].endswith("-revert") for n in re.findall(r"撤回\s*#(\d+)", m.get("body") or "")}
        st["merged"] = [{"number": m["number"], "issue": issue_of(m["headRefName"]), "merged_at": m["mergedAt"],
                         "reverted": m["number"] in reverted, "is_revert": m["headRefName"].endswith("-revert")} for m in merged]
        st["rejected"] = [{"pr": m["number"], "issue": issue_of(m["headRefName"])} for m in merged
                          if any(cfg.is_human(c["author"]) and first_line(c["body"]).startswith("[退回]") and unedited(c)
                                 for c in comments(m["comments"]))
                          and not re.search(rf"撤回\s*#{m['number']}(?!\d)", bodies)]
        rels = [r for r in gh("api", f"{base}/releases?per_page=10") if (r.get("author") or {}).get("login") == "github-actions[bot]"]
        st["last_release"] = {"tag": rels[0]["tag_name"], "published_at": rels[0]["published_at"]} if rels else {}
        runs = gh("api", f"{base}/commits/main/check-runs?check_name=full-test").get("check_runs", [])
        runs.sort(key=lambda r: r.get("started_at") or "")
        st["main_full_test"] = (runs[-1].get("conclusion") or "pending") if runs else ""
        st["main_sha"] = runs[-1].get("head_sha", "") if runs else ""
    return st


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="调度:下一步做什么")
    ap.add_argument("cmd", choices=["next", "state"])
    ap.add_argument("--side", choices=["dev", "pm", "review"], required=True)
    ap.add_argument("--state")
    args = ap.parse_args(argv)
    try:
        cfg = Config(Path.cwd())
        st = json.loads(Path(args.state).read_text(encoding="utf-8")) if args.state else gather(cfg, args.side)
        out = st if args.cmd == "state" else decide(cfg, st, args.side)
    except (UsageError, OSError, json.JSONDecodeError, KeyError) as e:
        print(f"dispatch: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
