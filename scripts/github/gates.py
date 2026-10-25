"""CI 与发布的闸门(docs/运营规则.md 1、4.1、6、9 章)。读 GitHub 的数据,只判断,不写任何东西。

    python scripts/github/gates.py pr --pr <PR 编号>                 # gate.yml:写成 PR 最新提交上的状态 gate
    python scripts/github/gates.py release --actor <运行者>          # release.yml 的闸门
    python scripts/github/gates.py release --dry-run                # 集成 Agent 事先列出没验收的 PR(不查运行者)
    python scripts/github/gates.py actor --actor <运行者>            # release.yml 的发布作业里再查一次运行者(重跑时)
    共通: --fixtures <文件夹>  用 JSON 文件代替 GitHub(测试用)
          --via-bot <dev|pm|review>  经 scripts/github/bot.sh 读 GitHub(Agent 的环境里没有人的 gh 登录)
          --now <ISO 时间>  代替现在的时间(测试用)

pr 的检查:
  1. PR 作者是开发 App(dev_bot)或人(approvers)。
  2. 分支 feat|fix/<N>-… 的 N 和正文的 `关联 #N` 一致;Issue #N 未关闭。
  3. 定版(撤回 PR 不查):以下之一
     a. Issue 带 `设计已批准`,且最后一次加它的是人;
     b. 人写了未被编辑的 `[定版]` 评论,且在最后一次 D1 结论之后;
     c. 自动定版:没有 `需人定版`;评审 App 最后的 D1 结论是未被编辑的 `[评审-通过] 方案`;
        从「它的时间」和「定版时间段的开始」两者较晚的那个算起,已过 [cycle] auto_approve_minutes 分钟。
  4. D2(撤回 PR 不查):评审 App 最后的 D2 结论是未被编辑的 `[评审-通过] 测试用例 范围:<sha256>`,
     指纹和 PR 当前提交上 docs/changes/<N>/ 的 范围.txt、01、03 一致(scope_hash)。
  D1、D2 的结论之后,PM / 开发 App 又写了那个阶段的 `[进度] … 完成` 时,旧结论不算(要重新评审)。
  需人定版:曾经加过、而最后去掉它的不是人时,当作还在。
  5. 评审 App 对当前提交的正式批准(state=APPROVED、commit_id=head),之后没有再要求修改;批准的正文里写着和当前一致的
     `范围:<指纹>`(正式评审删不掉,所以即使有人删了 Issue 上的评论,D3 也重新确认过范围和测试用例)。
  评审 App 建的 Issue(每周的架构建议)一律当作需人定版。
  6. 评审 App 对当前提交写了 `[测试-通过] <head>`,之后没有 `[测试-退回]`。
  7. PM App 对当前提交写了 `[PM-通过] <head>`,之后没有 `[PM-退回]`。
  撤回 PR = 分支 fix/<N>-revert 且正文有 `撤回 #<PR>`;那个 PR 上要有人写的 `[退回]`。是否只撤回了那个 PR,由 CI 的 scope 检查。
  --expect-head <sha>:PR 的最新提交不是它时退出码 2(gate.yml 用,避免把旧的判断写到新的提交上)。
release 的检查:
  1. 运行者是人(不以 [bot] 结尾)且在 approvers 里(--dry-run 时不查)。
  2. 起点 = 上一个由发布工作流(github-actions[bot])创建的 Release 的标签(没有就从头)。起点之后 main 上的每个提交都必须对上已合并的 PR,
     每个 PR 现在带 `已验收` 或 `免验收`,且最后一次加这个标签的是人。对不上 PR 的提交判 NG(不放过)。
  3. 要发布的提交上 full-test 成功。
dev_bot、pm_bot、review_bot 有相同的时拒绝运行:做的和审的在身份上必须分开。
退出码: 0 通过,1 不通过,2 用法错误或读不到数据。需要 Python 3.11 以上。
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print("gates: 需要 Python 3.11 以上(tomllib)", file=sys.stderr)
    sys.exit(2)

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tomllib  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

ACCEPT = ("已验收", "免验收")
RELEASER = "github-actions[bot]"


class UsageError(Exception):
    pass


class Config:
    def __init__(self, root: Path, text: str | None = None):
        if text is None:
            f = root / "project.toml"
            if not f.is_file():
                raise UsageError(f"找不到 {f}")
            text = f.read_text(encoding="utf-8")
        data = tomllib.loads(text)
        d = data.get("github", {})
        self.owner, self.repo = d.get("owner", ""), d.get("repo", "")
        self.approvers = [a for a in d.get("approvers", []) if a and "{{" not in a]
        self.dev_bot, self.pm_bot, self.review_bot = d.get("dev_bot", ""), d.get("pm_bot", ""), d.get("review_bot", "")
        if not self.approvers or "{{" in self.dev_bot + self.pm_bot + self.review_bot + self.owner + self.repo:
            raise UsageError("project.toml 的 [github] 还没填(owner、repo、approvers、dev_bot、pm_bot、review_bot)")
        if len({self.dev_bot, self.pm_bot, self.review_bot}) != 3:
            raise UsageError("dev_bot、pm_bot、review_bot 要是三个不同的 GitHub App(做的和审的必须分开)")
        c = data.get("cycle", {})
        m = re.fullmatch(r"([+-])(\d\d):(\d\d)", c.get("utc_offset", "+08:00"))
        if not m:
            raise UsageError("[cycle] utc_offset 要写成 +08:00 的形式")
        sign = 1 if m.group(1) == "+" else -1
        self.tz = timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))
        self.decide_from = _hm(c.get("decide_from", "09:00"))
        self.decide_until = _hm(c.get("decide_until", "21:00"))
        self.auto_minutes = int(c.get("auto_approve_minutes", 60))
        self.integrate_at = _hm(c.get("integrate_at", "17:30"))
        self.weekly_days = int(c.get("weekly_days", 7))

    def is_human(self, login: str) -> bool:
        return login in self.approvers and not login.endswith("[bot]")


def _hm(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d\d):(\d\d)", text)
    if not m:
        raise UsageError(f"[cycle] 的时间要写成 HH:MM(收到 {text})")
    return int(m.group(1)), int(m.group(2))


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def auto_deadline(cfg: Config, passed_at: datetime) -> datetime:
    """自动定版的时间:从 D1 通过的时间和定版时间段的开始两者较晚的那个算起,加等待时间。
    这样算出的时间超过当天的定版时间段(decide_until)时,改为第二天的开始 + 等待时间(人在时间段里总有完整的等待时间)。"""
    local = passed_at.astimezone(cfg.tz)
    start = local.replace(hour=cfg.decide_from[0], minute=cfg.decide_from[1], second=0, microsecond=0)
    until = local.replace(hour=cfg.decide_until[0], minute=cfg.decide_until[1], second=0, microsecond=0)
    wait = timedelta(minutes=cfg.auto_minutes)
    due = max(local, start) + wait
    return due if due <= until else start + timedelta(days=1) + wait


def first_line(body: str) -> str:
    return (body or "").strip().splitlines()[0].strip() if (body or "").strip() else ""


def unedited(c: dict) -> bool:
    return c.get("updated_at", c["created_at"]) == c["created_at"]


def last_verdict(comments: list[dict], author: str, kind: str) -> dict | None:
    """author 写的最后一条 `[评审-通过|评审-退回] <kind>` 评论。"""
    found = None
    for c in sorted(comments, key=lambda c: c["created_at"]):
        if c["author"] == author and re.match(rf"\[评审-(通过|退回)\]\s*{kind}", first_line(c["body"])):
            found = c
    return found


D2_FILES = ("范围.txt", "01-需求.md", "03-测试用例.md")


def scope_hash(get) -> str:
    """D2 的指纹:范围.txt、01、03 三个文件(换行统一成 \n,没有的文件当作空)。get(文件名) → 内容或 None。
    scripts/ci/verify.py 里有同样的计算(它在 CI 里单独运行,不能 import 这里),改的时候两边一起改。"""
    h = hashlib.sha256()
    for name in D2_FILES:
        h.update(name.encode("utf-8") + b"\0" + (get(name) or "").replace("\r\n", "\n").encode("utf-8") + b"\0")
    return h.hexdigest()


def fresh(comments: list[dict], verdict: dict | None, stage: str, author: str) -> bool:
    """结论之后,author 没有再写 `[进度] … <stage> 完成`(有的话说明改过了,旧结论不算;删掉后来的退回也救不活旧的通过)。"""
    if verdict is None:
        return False
    return not any(c["author"] == author and c["created_at"] > verdict["created_at"]
                   and first_line(c["body"]).startswith("[进度]") and re.search(rf"{stage}\s*完成", first_line(c["body"]))
                   for c in comments)


def design_status(cfg: Config, labels: list[str], comments: list[dict], now: datetime,
                  human_label: bool | None = None) -> tuple[bool, str]:
    """定版了没有。human_label=None 时只看标签在不在(调度用);gate 传入"标签是不是人加的"。"""
    d1 = last_verdict(comments, cfg.review_bot, "方案")
    if "设计已批准" in labels and human_label is not False:
        return True, "人定版(设计已批准)"
    for c in sorted(comments, key=lambda c: c["created_at"], reverse=True):
        if cfg.is_human(c["author"]) and first_line(c["body"]).startswith("[定版]") and unedited(c):
            if d1 is None or c["created_at"] > d1["created_at"]:
                return True, f"人定版({first_line(c['body'])[:30]})"
            break
    if "需人定版" in labels:
        return False, "需人定版:只能由人定版(加 设计已批准 或写 [定版])"
    if d1 is None or not first_line(d1["body"]).startswith("[评审-通过]") or not fresh(comments, d1, "方案", cfg.pm_bot):
        return False, "评审 App 还没有通过最新的方案(D1)"
    if not unedited(d1):
        return False, "D1 的通过评论被编辑过,不算数"
    due = auto_deadline(cfg, parse_time(d1["created_at"]))
    if now < due:
        return False, f"等人定版,{due.strftime('%m-%d %H:%M')} 起自动按 V1"
    return True, f"自动定版(V1,{due.strftime('%m-%d %H:%M')} 起)"


def head_verdict(reviews: list[dict], author: str, mark: str, head: str) -> str:
    """author 对 head 写的最后一条 `[<mark>-通过|退回] <head>` 评审:'通过' / '退回' / ''。"""
    v = ""
    for r in sorted(reviews, key=lambda r: r["submitted_at"]):
        m = re.match(rf"\[{mark}-(通过|退回)\]\s*([0-9a-f]+)", first_line(r["body"]))
        if r["author"] == author and m and len(m.group(2)) >= 7 and head.startswith(m.group(2)) and r.get("commit_id", head) == head:
            v = m.group(1)
    return v


def approved_review(reviews: list[dict], author: str, head: str) -> dict | None:
    """author 对 head 的最后一个正式结论是批准时,返回那个评审。"""
    last = None
    for r in sorted(reviews, key=lambda r: r["submitted_at"]):
        if r["author"] == author and r["state"] in ("APPROVED", "CHANGES_REQUESTED"):
            last = r
    return last if last and last["state"] == "APPROVED" and last["commit_id"] == head else None


def approval(reviews: list[dict], author: str, head: str) -> str:
    v = ""
    for r in sorted(reviews, key=lambda r: r["submitted_at"]):
        if r["author"] != author:
            continue
        if r["state"] == "APPROVED" and r["commit_id"] == head:
            v = "APPROVED"
        elif r["state"] == "CHANGES_REQUESTED":
            v = "CHANGES_REQUESTED"
    return v


# ---------------------------------------------------------------------------------------------------------------------------------
# 数据来源:GitHub(gh api)或 fixtures(测试)

class Fixtures:
    def __init__(self, folder: Path):
        self.folder = folder

    def _load(self, name, default=None):
        p = self.folder / name
        if not p.is_file():
            if default is not None:
                return default
            raise UsageError(f"fixtures 里没有 {name}")
        return json.loads(p.read_text(encoding="utf-8"))

    def pr(self, n):
        return self._load(f"pr_{n}.json")

    def reviews(self, n):
        return self._load(f"reviews_{n}.json")

    def issue(self, n):
        return self._load(f"issue_{n}.json")

    def events(self, n):
        return self._load(f"events_{n}.json")

    def comments(self, n):
        return self._load(f"comments_{n}.json", [])

    def file_at(self, path, ref):
        return self._load("files.json", {}).get(path)

    def pr_comments(self, n):
        return self._load(f"comments_{n}.json", [])

    def now(self):
        return parse_time(self._load("now.json", {"now": datetime.now(timezone.utc).isoformat()})["now"])

    def last_release_tag(self):
        return self._load("last_release.json").get("tag", "")

    def commits(self, since):
        return self._load("commits.json")

    def check(self, name):
        return self._load("checks.json", {}).get(name) or ""


class GitHub:
    def __init__(self, cfg: Config, via_bot: str = "", release_ref: str = "HEAD"):
        self.base = f"repos/{cfg.owner}/{cfg.repo}"
        self.release_ref = release_ref          # 发布工作流:检出的 HEAD;集成 Agent 的 --dry-run:origin/main
        self.gh = ["bash", "scripts/github/bot.sh", via_bot, "gh"] if via_bot else ["gh"]

    def _run(self, args):
        r = subprocess.run(self.gh + args, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise UsageError(f"gh {' '.join(args[:2])}: {r.stderr.strip()[:200]}")
        return r.stdout

    def _api(self, path, paginate=True):
        out = self._run(["api", path, "--paginate", "--slurp"] if paginate else ["api", path])
        data = json.loads(out or "null")
        if paginate:            # --slurp: a list of pages; list pages are joined, an object page is returned as is
            return [x for page in data for x in page] if data and isinstance(data[0], list) else (data[0] if data else {})
        return data

    def pr(self, n):
        d = self._api(f"{self.base}/pulls/{n}", paginate=False)
        return {"number": n, "author": d["user"]["login"], "head_sha": d["head"]["sha"], "head_ref": d["head"]["ref"],
                "body": d.get("body") or ""}

    def files(self, n):
        return [f["filename"] for f in self._api(f"{self.base}/pulls/{n}/files")]

    def reviews(self, n):
        return [{"author": (r.get("user") or {}).get("login", ""), "state": r["state"], "commit_id": r.get("commit_id") or "",
                 "submitted_at": r.get("submitted_at") or "", "body": r.get("body") or ""}
                for r in self._api(f"{self.base}/pulls/{n}/reviews")]

    def issue(self, n):
        d = self._api(f"{self.base}/issues/{n}", paginate=False)
        return {"number": n, "state": d["state"], "labels": [l["name"] for l in d.get("labels", [])],
                "author": (d.get("user") or {}).get("login", "")}

    def events(self, n):
        return [{"event": e["event"], "label": (e.get("label") or {}).get("name", ""), "actor": (e.get("actor") or {}).get("login", ""),
                 "created_at": e["created_at"]} for e in self._api(f"{self.base}/issues/{n}/events")]

    def comments(self, n):
        return [{"author": (c.get("user") or {}).get("login", ""), "body": c.get("body") or "", "created_at": c["created_at"],
                 "updated_at": c.get("updated_at") or c["created_at"]} for c in self._api(f"{self.base}/issues/{n}/comments")]

    def pr_comments(self, n):
        return self.comments(n)              # PR 的评论也是 Issue 的评论

    def file_at(self, path, ref):
        r = subprocess.run(self.gh + ["api", f"{self.base}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"],
                           capture_output=True, text=True, encoding="utf-8")
        return r.stdout if r.returncode == 0 else None

    def now(self):
        return datetime.now(timezone.utc)

    def last_release_tag(self):
        for rel in self._api(f"{self.base}/releases"):
            if not rel.get("draft") and (rel.get("author") or {}).get("login") == RELEASER:
                return rel["tag_name"]
        return ""

    def commits(self, since):
        head = self.release_ref
        rng = f"{since}..{head}" if since else head
        r = subprocess.run(["git", "log", "--first-parent", "--format=%H", rng], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise UsageError(f"git log {rng}: {r.stderr.strip()[:200]}")
        out = []
        for sha in r.stdout.split():
            prs = [p["number"] for p in self._api(f"{self.base}/commits/{sha}/pulls") if p.get("merged_at")]
            out.append({"sha": sha, "prs": prs})
        return out

    def check(self, name):
        sha = subprocess.run(["git", "rev-parse", self.release_ref], capture_output=True, text=True).stdout.strip()
        runs = self._api(f"{self.base}/commits/{sha}/check-runs?check_name={name}", paginate=False).get("check_runs", [])
        runs.sort(key=lambda r: r.get("started_at") or "")
        return (runs[-1].get("conclusion") or runs[-1].get("status") or "") if runs else ""


# ---------------------------------------------------------------------------------------------------------------------------------

def human_label(cfg: Config, src, n: int, names: tuple[str, ...]) -> tuple[bool, str]:
    """Issue/PR n 现在带 names 中的某个标签,且最后一次加该标签的是人。"""
    present = [l for l in src.issue(n)["labels"] if l in names]
    if not present:
        return False, f"#{n} 没有 {' / '.join(names)}"
    for label in present:
        adds = [e for e in src.events(n) if e["event"] == "labeled" and e["label"] == label]
        if adds and cfg.is_human(sorted(adds, key=lambda e: e["created_at"])[-1]["actor"]):
            return True, f"#{n} 有人加的 {label}"
    return False, f"#{n} 的 {' / '.join(present)} 不是人加的(只算 approvers 加的)"


def needs_human(cfg: Config, src, n: int, labels: list[str]) -> bool:
    """带着 需人定版,或它曾经加过、而最后去掉它的不是人。"""
    if "需人定版" in labels:
        return True
    evs = sorted((e for e in src.events(n) if e["label"] == "需人定版"), key=lambda e: e["created_at"])
    removed = [e for e in evs if e["event"] == "unlabeled"]
    return bool(evs) and not (removed and cfg.is_human(removed[-1]["actor"]))


CODEOWNERS = ".github/CODEOWNERS"


def _glob_re(pat: str) -> re.Pattern:
    """CODEOWNERS 的模式 → 正则:* 不跨 /,** 跨。"""
    out, i = [], 0
    while i < len(pat):
        if pat.startswith("**", i):
            out.append(".*")
            i += 2
        elif pat[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pat[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pat[i]))
            i += 1
    return re.compile("".join(out))


def codeowners() -> list[str]:
    try:
        with open(CODEOWNERS, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return []
    pats = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pats.append(line.split()[0])
    return pats


def framework_only(files: list[str]) -> bool:
    """改动全在代码负责人的文件里 = 框架 PR(docs/运营规则.md 4 章)。

    依据只有 .github/CODEOWNERS,不另立清单(两份会漂)。docs/changes/ 和共用文档不算 —— 每个 PR 都会加。
    """
    files = [f for f in files if not f.startswith("docs/changes/")
             and f not in ("docs/回归清单.md", "docs/术语表.md")]
    pats = codeowners()
    if not files or not pats:
        return False
    for f in files:
        hit = False
        for pat in pats:
            anchored, p = pat.startswith("/"), pat.lstrip("/")
            dir_only = p.endswith("/")
            p = p.rstrip("/")
            if dir_only:
                hit = f.startswith(p + "/")
            elif anchored:
                hit = bool(_glob_re(p).fullmatch(f))
            else:
                hit = bool(_glob_re(p).fullmatch(f.rsplit("/", 1)[-1]))
            if hit:
                break
        if not hit:
            return False
    return True


def check_pr(cfg: Config, src, n: int, now: datetime | None = None, expect_head: str = "") -> tuple[list[str], list[str]]:
    ok, ng = [], []
    pr = src.pr(n)
    head = pr["head_sha"]
    if expect_head and head != expect_head:
        raise UsageError(f"PR #{n} 的最新提交已经不是 {expect_head[:12]}(有新的推送,交给下一次判断)")
    now = now or src.now()
    # 框架 PR(只改代码负责人的文件):没有 REQ 可追溯,也不会有定版、D2、测试、PM 验收 —— 那几道闸是给需求的。
    # 它的关卡是人批准(4 章),所以这里只要求"作者合规 + 代码负责人批准了当前提交",其余跳过。
    # 这样框架 PR 不用再 --admin 硬绕;改到需求代码的 PR 照旧走完整流程。
    files = getattr(src, "files", None)
    if files and framework_only(files(n)):
        ok = []
        if pr["author"] == cfg.dev_bot or cfg.is_human(pr["author"]):
            ok.append(f"作者 {pr['author']}")
        else:
            ng.append(f"作者 {pr['author']} 既不是开发 App 也不是批准人")
        if any(cfg.is_human(r["author"]) and r["state"] == "APPROVED" and r["commit_id"] == head for r in src.reviews(n)):
            ok.append(f"框架 PR:代码负责人批准了当前提交 {head[:12]}")
        else:
            ng.append(f"框架 PR:还没有代码负责人对当前提交 {head[:12]} 的批准(框架文件要人批准)")
        return ok, ng
    if pr["author"] == cfg.dev_bot or cfg.is_human(pr["author"]):
        ok.append(f"作者 {pr['author']}")
    else:
        ng.append(f"作者 {pr['author']} 既不是开发 App 也不是批准人")
    m = re.search(r"关联\s*#(\d+)", pr["body"])
    b = re.match(r"^(?:feat|fix)/(\d+)-", pr.get("head_ref", ""))
    revert = bool(re.fullmatch(r"fix/\d+-revert", pr.get("head_ref", "")) and re.search(r"撤回\s*#\d+", pr["body"]))
    if not m:
        ng.append("正文里没有 `关联 #<编号>`")
    elif not b or b.group(1) != m.group(1):
        ng.append(f"分支 {pr.get('head_ref', '?')} 的编号和 `关联 #{m.group(1)}` 不一致")
    else:
        i = int(m.group(1))
        issue = src.issue(i)
        if revert:                         # 原 Issue 可能已在上线后关闭
            t = int(re.search(r"撤回\s*#(\d+)", pr["body"]).group(1))
            target = re.match(r"^(?:feat|fix)/(\d+)-", src.pr(t).get("head_ref", ""))
            if not target or int(target.group(1)) != i:
                ng.append(f"撤回 PR:PR #{t} 不是 #{i} 的 PR(只能撤回同一个 Issue 的 PR)")
            elif any(cfg.is_human(c["author"]) and first_line(c["body"]).startswith("[退回]") and unedited(c) for c in src.pr_comments(t)):
                ok.append(f"撤回 PR #{t}(人写了 [退回];不查定版和 D2;只撤回由 scope 检查)")
            else:
                ng.append(f"撤回 PR:PR #{t} 上没有人写的(未被编辑的)[退回]")
        elif issue.get("state") != "open":
            ng.append(f"#{i} 已关闭(不能借用关闭的 Issue 的定版)")
        else:
            comments = src.comments(i)
            human_needed = needs_human(cfg, src, i, issue["labels"]) or issue.get("author") == cfg.review_bot
            labels = issue["labels"] + (["需人定版"] if human_needed and "需人定版" not in issue["labels"] else [])
            labeled = human_label(cfg, src, i, ("设计已批准",))[0] if "设计已批准" in labels else None
            good, msg = design_status(cfg, labels, comments, now, labeled)
            if "设计已批准" in labels and labeled is False and not good:
                msg = f"#{i} 的 设计已批准 不是人加的;" + msg
            (ok if good else ng).append("定版: " + msg)
            d2 = last_verdict(comments, cfg.review_bot, "测试用例")
            hm = re.search(r"范围[:：]\s*([0-9a-f]{64})", first_line(d2["body"])) if d2 else None
            if not d2 or not first_line(d2["body"]).startswith("[评审-通过]") or not fresh(comments, d2, "测试用例", cfg.dev_bot):
                ng.append("D2: 评审 App 还没有通过最新的测试用例")
            elif not unedited(d2) or not hm:
                ng.append("D2: 通过评论被编辑过或没有写 范围:<sha256>")
            else:
                if src.file_at(f"docs/changes/{i}/范围.txt", head) is None:
                    ng.append(f"D2: 当前提交上没有 docs/changes/{i}/范围.txt")
                elif scope_hash(lambda f: src.file_at(f"docs/changes/{i}/{f}", head)) != hm.group(1):
                    ng.append("D2: 范围.txt、01 或 03 在评审之后被改过(指纹不一致),要重新做 D2")
                else:
                    ok.append("D2: 测试用例通过,范围的指纹一致")
                    a = approved_review(src.reviews(n), cfg.review_bot, head)
                    if a and not re.search(rf"范围[:：]\s*{hm.group(1)}", a["body"]):
                        ng.append("D3: 评审 App 的批准正文里没有和当前一致的 范围:<指纹>(D3 要重新确认范围和测试用例)")
    reviews = src.reviews(n)
    v = approval(reviews, cfg.review_bot, head)
    if v == "APPROVED":
        ok.append(f"评审 App 批准了当前提交 {head[:12]}")
    elif v == "CHANGES_REQUESTED":
        ng.append("评审 App 最后的结论是要求修改")
    else:
        ng.append(f"没有评审 App({cfg.review_bot})对当前提交 {head[:12]} 的正式批准")
    for who, mark, name in ((cfg.review_bot, "测试", "测试"), (cfg.pm_bot, "PM", "PM 验收")):
        t = head_verdict(reviews, who, mark, head)
        if t == "通过":
            ok.append(f"{name}通过(当前提交)")
        elif t == "退回":
            ng.append(f"{name}最后的结论是退回")
        else:
            ng.append(f"没有 {who} 对当前提交 {head[:12]} 的 [{mark}-通过]")
    return ok, ng


def check_actor(cfg: Config, actor: str) -> tuple[list[str], list[str]]:
    if cfg.is_human(actor):
        return [f"运行者 {actor} 是批准人"], []
    return [], [f"运行者 {actor} 不是批准人(机器人和名单外的人不能发布)"]


def check_release(cfg: Config, src, actor: str | None) -> tuple[list[str], list[str], str]:
    ok, ng = check_actor(cfg, actor) if actor is not None else ([], [])
    since = src.last_release_tag()
    commits = src.commits(since)
    if not commits:
        ng.append(f"{since or '开始'} 之后 main 上没有新的提交")
    prs = []
    for c in commits:
        if not c["prs"]:
            ng.append(f"提交 {c['sha'][:12]} 对不上已合并的 PR(main 只应通过 PR 变化)")
        prs += [n for n in c["prs"] if n not in prs]
    for n in prs:
        good, msg = human_label(cfg, src, n, ACCEPT)
        (ok if good else ng).append(msg)
    full = src.check("full-test")
    (ok if full == "success" else ng).append(f"要发布的提交上 full-test: {full or '没有运行'}")
    return ok, ng, since


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="CI 与发布的闸门")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pr"); p.add_argument("--pr", type=int, required=True); p.add_argument("--fixtures"); p.add_argument("--now")
    p.add_argument("--expect-head", default="")
    p.add_argument("--via-bot", choices=["dev", "pm", "review"], default="")
    r = sub.add_parser("release"); r.add_argument("--actor"); r.add_argument("--dry-run", action="store_true"); r.add_argument("--fixtures")
    r.add_argument("--via-bot", choices=["dev", "pm", "review"], default="")
    a = sub.add_parser("actor"); a.add_argument("--actor", required=True)
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        cfg = Config(Path.cwd())
        if args.cmd == "actor":
            ok, ng = check_actor(cfg, args.actor)
            title = "运行者"
        else:
            ref = "origin/main" if args.cmd == "release" and args.dry_run else "HEAD"
            src = Fixtures(Path(args.fixtures)) if args.fixtures else GitHub(cfg, args.via_bot, ref)
            if args.cmd == "pr":
                ok, ng = check_pr(cfg, src, args.pr, parse_time(args.now) if args.now else None, args.expect_head)
                title = f"PR #{args.pr}"
            else:
                if not args.dry_run and not args.actor:
                    raise UsageError("release 需要 --actor(或 --dry-run)")
                ok, ng, since = check_release(cfg, src, None if args.dry_run else args.actor)
                title = f"发布(自 {since or '开始'})"
    except UsageError as e:
        print(f"gates: {e}", file=sys.stderr)
        return 2
    for line in ok:
        print(f"  OK  {line}")
    for line in ng:
        print(f"  NG  {line}")
    print(f"gates: {title}: {'通过' if not ng else '不通过'}(OK {len(ok)} / NG {len(ng)})")
    if args.cmd == "release" and args.dry_run:
        return 0
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
