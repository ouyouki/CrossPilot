"""一个环境的循环(由 scripts/agent/run.sh 启动;docs/运营规则.md 5 章)。

    bash scripts/agent/run.sh <dev|pm|review> [--until HH:MM] [--once] [--dry-run] [--state <JSON>]

每一轮:
  1. 查上限:今天的运行次数([runner] max_runs_per_day)和等价 Token([runner] daily_tokens)。到了就停止(第二天恢复);到 80% 在日志里警告。
  2. 问调度(scripts/agent/dispatch.py)下一步做什么。没有就隔 interval_seconds 再看(--once 时结束)。
  3. 同一件事(调度给的 key 相同 = 上次运行之后没有进展)第 max_retries + 1 次、或这件事累计的 Token 超过 issue_tokens:
     给 Issue 加 `阻塞` 并写 `[阻塞]`,跳过,等人处理。
  4. 按 [runner.commands] 的模板启动 harness(超时 timeout_minutes),输出写到 tmp/agent-logs/<日期>/,从输出里读 Token 用量。
等价 Token = 输入 + 输出 + 缓存写入 + 缓存命中 / 10(缓存命中便宜)。读不到用量时按 unknown_run_tokens 计入。
同一个环境同时只能有一个循环(锁文件 tmp/agent-<环境>.lock,每轮更新;超过「一次运行的最长时间 + 等待 + 10 分钟」没更新的视为残留)。
环境变量 BOT_ROLE 必须等于 <环境>。加 `阻塞` 时把这件事的重试次数和累计 Token 清零(人去掉 `阻塞` 就重新开始)。
/integrate、/wrapup 这类不属于某个 Issue 的事(issue 0)不计每件事的 Token;连续没有进展时当天跳过它(不停止循环)。
--dry-run 只显示要运行的命令,不启动 Agent、不写 GitHub、不计次数。--state 用 JSON 文件代替 GitHub(测试用)。
记录:tmp/agent-<环境>-state.json(次数、Token、重试;日期变了就清零,每件事的累计 Token 保留);
      tmp/agent-logs/runs.jsonl(每次运行、阻塞、跳过各一行;scripts/agent/report.py 把它做成看板)。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "agent"))
sys.path.insert(0, str(ROOT / "scripts" / "github"))
from dispatch import decide, gather  # noqa: E402
from gates import Config, UsageError  # noqa: E402



def log(msg: str) -> None:
    print(f"run: {datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)


def usage_tokens(text: str) -> int | None:
    """从 harness 的 JSON 输出里读等价 Token。Claude Code: 结果的 modelUsage(含子 Agent)或 usage;OpenCode: 各事件的 tokens。"""
    found = []

    def eq(i=0, o=0, w=0, r=0):
        return int(i) + int(o) + int(w) + int(r) // 10

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("modelUsage"), dict) and x["modelUsage"]:
                found.append(sum(eq(m.get("inputTokens", 0), m.get("outputTokens", 0), m.get("cacheCreationInputTokens", 0),
                                    m.get("cacheReadInputTokens", 0)) for m in x["modelUsage"].values()))
                return
            u = x.get("usage")
            if isinstance(u, dict) and "input_tokens" in u and x.get("type") == "result":
                found.append(eq(u.get("input_tokens", 0), u.get("output_tokens", 0), u.get("cache_creation_input_tokens", 0),
                                u.get("cache_read_input_tokens", 0)))
                return
            t = x.get("tokens")
            if isinstance(t, dict) and "input" in t:
                c = t.get("cache") or {}
                found.append(eq(t.get("input", 0), int(t.get("output", 0)) + int(t.get("reasoning", 0)), c.get("write", 0), c.get("read", 0)))
                return
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    try:
        walk(json.loads(text))
    except json.JSONDecodeError:
        for line in text.splitlines():
            try:
                walk(json.loads(line))
            except json.JSONDecodeError:
                pass
    return sum(found) if found else None


def record(**kw) -> None:
    """在 tmp/agent-logs/runs.jsonl 追加一行(看板用)。"""
    f = ROOT / "tmp" / "agent-logs" / "runs.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"time": datetime.now().astimezone().isoformat(timespec="seconds"), **kw}, ensure_ascii=False) + "\n")


def build(template: list[str], t: dict, max_turns: int, domains: list[str] = ()) -> list[str]:
    name, *args = t["command"].lstrip("/").split()
    out = []
    for part in template:
        if part == "{args}":
            out += args
        elif part == "{webfetch}":
            out += [f"WebFetch(domain:{d})" for d in domains]
        else:
            out.append(part.format(prompt=t["command"], name=name, agent=t["agent"], max_turns=max_turns, args=" ".join(args)))
    return out


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="一个环境的 Agent 循环")
    ap.add_argument("side", choices=["dev", "pm", "review"])
    ap.add_argument("--until")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state")
    args = ap.parse_args(argv)
    side = args.side
    if os.environ.get("BOT_ROLE") != side:
        print(f"run: 这个环境的 BOT_ROLE 是 {os.environ.get('BOT_ROLE') or '(没设)'},不能运行 {side} 的循环", file=sys.stderr)
        return 2
    os.chdir(ROOT)
    try:
        cfg = Config(ROOT)
        rc = tomllib.loads((ROOT / "project.toml").read_text(encoding="utf-8")).get("runner", {})
        harness = rc.get("harness", "claude")
        template = rc.get("commands", {}).get(harness)
        if not template:
            raise UsageError(f"[runner.commands] 里没有 {harness} 的命令模板")
        domains = rc.get("web_domains", [])
        if any(not re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", d) for d in domains):
            raise UsageError("[runner] web_domains 只写小写的域名(例 docs.python.org),不写 https:// 和路径")
    except (UsageError, OSError, tomllib.TOMLDecodeError) as e:
        print(f"run: {e}", file=sys.stderr)
        return 2
    per = lambda key, default: (rc.get(key) or {}).get(side, default)  # noqa: E731
    max_runs, max_turns, daily = per("max_runs_per_day", 60), per("max_turns", 40), per("daily_tokens", 10_000_000)
    issue_cap, unknown = rc.get("issue_tokens", 5_000_000), rc.get("unknown_run_tokens", 400_000)
    max_retries, interval, timeout = rc.get("max_retries", 3), rc.get("interval_seconds", 120), rc.get("timeout_minutes", 30) * 60

    tmp = ROOT / "tmp"
    tmp.mkdir(exist_ok=True)
    lock = tmp / f"agent-{side}.lock"
    stale = timeout + interval + 600
    if lock.exists() and time.time() - lock.stat().st_mtime > stale:
        lock.unlink(missing_ok=True)                     # left over from a loop that died
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(f"run: {side} 的循环已经在运行({lock})。确认没有在运行后删除这个文件", file=sys.stderr)
        return 1
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    try:
        return loop(args, cfg, side, template, max_runs, max_turns, daily, issue_cap, unknown, max_retries, interval, timeout, lock, domains)
    finally:
        lock.unlink(missing_ok=True)


def run_harness(cmd: list[str], timeout: int) -> tuple[str, object]:
    """启动 harness;超时时连同它的子进程一起结束。"""
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
    try:
        out, err = proc.communicate(timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            os.killpg(proc.pid, 9)
        try:
            out, err = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:         # a child left the group and still holds the pipes
            out, err = b"", b""
        code = "超时"
    return (out or b"").decode("utf-8", "replace") + "\n" + (err or b"").decode("utf-8", "replace"), code


def loop(args, cfg, side, template, max_runs, max_turns, daily, issue_cap, unknown, max_retries, interval, timeout, lock, domains) -> int:
    state_file = ROOT / "tmp" / f"agent-{side}-state.json"
    while True:
        lock.touch()
        today = datetime.now(cfg.tz).strftime("%Y-%m-%d")
        try:
            st = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            st = {}
        if st.get("date") != today:
            st = {"date": today, "runs": 0, "tokens": 0, "tries": {}, "skip": [], "issue_tokens": st.get("issue_tokens", {})}
        if st["runs"] >= max_runs or st["tokens"] >= daily:
            log(f"已到今天的上限(运行 {st['runs']}/{max_runs} 次,Token {st['tokens']:,}/{daily:,})。明天恢复;要提高就改 project.toml 的 [runner]")
            return 1
        if args.until and datetime.now(cfg.tz).strftime("%H:%M") >= args.until:
            log(f"到了 {args.until},结束")
            return 0
        try:
            world = json.loads(Path(args.state).read_text(encoding="utf-8")) if args.state else gather(cfg, side)
            t = decide(cfg, world, side, set(st.get("skip", [])))
        except (UsageError, OSError, json.JSONDecodeError, KeyError) as e:
            log(f"读不到状态: {e}")
            if args.once:
                return 2
            time.sleep(interval)
            continue
        if not t.get("command"):
            log(t.get("reason", "没有可做的事"))
            if args.once:
                return 0
            time.sleep(interval)
            continue
        cmd = build(template, t, max_turns, domains)
        if args.dry_run:
            log(f"dry-run: {t['agent']}: {subprocess.list2cmdline(cmd)}")
            return 0
        issue = str(t.get("issue") or 0)
        st["tries"][t["key"]] = st["tries"].get(t["key"], 0) + 1
        if st["tries"][t["key"]] > max_retries or (issue != "0" and st["issue_tokens"].get(issue, 0) >= issue_cap):
            why = (f"同一件事连续 {max_retries} 次没有进展" if st["tries"][t["key"]] > max_retries
                   else f"这件事累计 Token {st['issue_tokens'].get(issue, 0):,} 超过 {issue_cap:,}")
            if issue == "0":
                log(f"{t['command']}: {why}。今天跳过这件事,请人看 tmp/agent-logs/")
                record(event="skip", side=side, command=t["command"], issue=0, why=why)
                st.setdefault("skip", []).append(t["key"])
                state_file.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
                continue
            if not block(side, issue, f"{t['command']}: {why}"):
                log(f"#{issue}: 加不上 阻塞,停止循环(避免反复写评论),请人看")
                return 1
            record(event="block", side=side, command=t["command"], issue=int(issue), why=why)
            st["tries"].pop(t["key"], None)
            st["issue_tokens"].pop(issue, None)
            state_file.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
            if args.once:
                return 1
            time.sleep(interval)
            continue
        logdir = ROOT / "tmp" / "agent-logs" / today
        logdir.mkdir(parents=True, exist_ok=True)
        logf = logdir / f"{datetime.now().strftime('%H%M%S')}-{side}-{t['command'].lstrip('/').split()[0]}.log"
        log(f"{t['agent']}: {t['command']}(日志 {logf.relative_to(ROOT)})")
        started = time.time()
        try:
            out, code = run_harness(cmd, timeout)
        except OSError as e:
            log(f"启动不了 harness: {e}")
            return 2
        logf.write_text(out, encoding="utf-8")
        used = usage_tokens(out)
        known, used = used is not None, unknown if used is None else used
        record(event="run", side=side, command=t["command"], issue=int(issue), tokens=used, known=known, code=str(code),
               seconds=round(time.time() - started), tries=st["tries"][t["key"]], log=str(logf.relative_to(ROOT)))
        st["runs"] += 1
        st["tokens"] += used
        if issue != "0":
            st["issue_tokens"][issue] = st["issue_tokens"].get(issue, 0) + used
        state_file.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
        log(f"结束(退出码 {code},Token {used:,};今天 {st['runs']} 次,{st['tokens']:,})")
        if st["tokens"] >= daily * 0.8 or st["runs"] >= max_runs * 0.8:
            log("警告:今天的用量已超过上限的 80%")
        if args.once:
            return 0


def block(side: str, issue: str, why: str) -> bool:
    bot = ["bash", "scripts/github/bot.sh", side, "gh"]
    if subprocess.run(bot + ["issue", "edit", issue, "--add-label", "阻塞"], capture_output=True).returncode != 0:
        return False
    body = f"[阻塞] {why}。调度已跳过这件事;人确认后去掉 `阻塞` 标签即可恢复。"
    subprocess.run(bot + ["issue", "comment", issue, "--body-file", "-"], input=body, capture_output=True, text=True, encoding="utf-8")
    log(f"#{issue}: {why} → 已加 阻塞")
    return True


if __name__ == "__main__":
    sys.exit(main())
