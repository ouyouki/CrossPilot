"""合并前的检验(docs/运营规则.md 4.1 章)。CI 用 main 上的这个文件运行,PR 改不了它。

    python scripts/ci/verify.py scope --base origin/main [--branch feat/3-x]   # 改动的文件都在 范围.txt 里
    python scripts/ci/verify.py trace --base origin/main [--branch feat/3-x]   # 需求 → 用例 → 自动测试或 OK 的证据
    python scripts/ci/verify.py scope-hash --issue 3 [--ref origin/feat/3-x]  # 显示 范围.txt、01、03 的指纹(评审 Agent 写进 D2)

--branch 省略时用 GITHUB_HEAD_REF 或当前分支。分支名 feat|fix/<N>-… 决定 Issue 编号 N。project.toml 从 --base 读(PR 改不了设置)。
scope: 改动(--base 和 HEAD 的分叉点 → HEAD)的每个文件,都要匹配 docs/changes/<N>/范围.txt 的某一行(glob,** 可跨文件夹),
       或在 docs/changes/<N>/ 里,或是 docs/回归清单.md、docs/术语表.md、docs/决策/ 下(全项目共用的文档,随时可以补)。改名按"删除 + 新增"算(两个路径都要在范围里)。
       撤回 PR(分支 fix/<N>-revert;提交信息有且只有一个 撤回 #<PR>,和环境变量 PR_BODY 里写的一致):改动的文件都是那个 PR 改过的,
       且这些文件的内容等于"在分叉点上把那个 PR 的合并反向应用"的结果。
trace: 01 的每个 REQ 至少有一个 03 的有效用例;03 的每个有效用例:方式=自动 → 测试代码([trace] test_globs)里有用例 ID;
       方式=手动 → 04 里结果是 OK;04 里没有 NG。
       已有的自动用例不能消失:分叉点的测试代码里有的用例 ID,HEAD 的测试代码里也要有,
       除非这个 Issue 的 03 里有那一行且「状态」是 取消(理由写在备注里,D2 评审)。已有的测试文件里断言变少时只提示(D3 评审看)。
       撤回 PR 不查(01 被一起撤掉了)。
退出码: 0 通过,1 不通过,2 用法错误。
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print("verify: 需要 Python 3.11 以上", file=sys.stderr)
    sys.exit(2)

import argparse  # noqa: E402
import fnmatch  # noqa: E402
import hashlib  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tomllib  # noqa: E402


class UsageError(Exception):
    pass


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-c", "core.quotepath=off", *args], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise UsageError(f"git {' '.join(args[:2])}: {r.stderr.strip()[:200]}")
    return r.stdout if r.returncode == 0 else ""


def show(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def glob_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def scope_hash(get) -> str:
    """D2 的指纹:范围.txt、01、03(换行统一成 LF,没有的文件当作空)。和 scripts/github/gates.py 的 scope_hash 相同,改的时候两边一起改。"""
    h = hashlib.sha256()
    for name in ("范围.txt", "01-需求.md", "03-测试用例.md"):
        h.update(name.encode("utf-8") + b"\0" + (get(name) or "").replace("\r\n", "\n").encode("utf-8") + b"\0")
    return h.hexdigest()


def issue_of(branch: str) -> tuple[int, bool]:
    m = re.match(r"^(?:feat|fix)/(\d+)-", branch)
    if not m:
        raise UsageError(f"分支名 {branch} 不是 feat|fix/<编号>-<短名>")
    return int(m.group(1)), bool(re.fullmatch(r"fix/\d+-revert", branch))


def changed(base: str) -> list[str]:
    return [f for f in git("diff", "--name-only", "--no-renames", f"{base}...HEAD").splitlines() if f]


def check_revert(base: str, files: list[str]) -> tuple[list[str], list[str]]:
    msg = git("log", "--format=%B", f"{base}..HEAD")
    nums = set(re.findall(r"撤回\s*#(\d+)", msg))
    body = set(re.findall(r"撤回\s*#(\d+)", os.environ.get("PR_BODY", ""))) if "PR_BODY" in os.environ else nums
    if len(nums) != 1 or body != nums:
        return [], ["撤回 PR:提交信息里要有且只有一个 `撤回 #<PR>`,并和 PR 正文写的一致"]
    m = re.match(r"(\d+)", nums.pop())
    target = [l.split()[0] for l in git("log", "--first-parent", "--format=%H %s", base).splitlines()
              if re.search(rf"\(#{m.group(1)}\)\s*$", l)]
    if not target:
        return [], [f"{base} 上找不到 PR #{m.group(1)} 合并的提交(标题以 (#{m.group(1)}) 结尾)"]
    sha = target[0]
    theirs = set(f for f in git("diff", "--name-only", "--no-renames", f"{sha}^", sha).splitlines() if f)
    extra = [f for f in files if f not in theirs]
    if extra:
        return [], [f"撤回 PR 改了原 PR 没改的文件: {f}" for f in extra]
    # 期望的结果 = 分叉点上把那个合并反向应用(后来别的 PR 也改过同一个文件时也成立)
    mb = git("merge-base", base, "HEAD").strip()
    index = os.path.join(git("rev-parse", "--git-dir").strip(), "verify-revert-index")
    env = dict(os.environ, GIT_INDEX_FILE=index)
    try:
        subprocess.run(["git", "read-tree", mb], env=env, check=True, capture_output=True)
        patch = subprocess.run(["git", "diff", "--binary", "--no-renames", sha, f"{sha}^"], capture_output=True, check=True).stdout
        if subprocess.run(["git", "apply", "--cached"], input=patch, env=env, capture_output=True).returncode != 0:
            return [], [f"PR #{m.group(1)} 的改动不能干净地反向应用到 {base} 上(后来的改动冲突),请人处理"]
        tree = subprocess.run(["git", "write-tree"], env=env, capture_output=True, text=True, check=True).stdout.strip()
    finally:
        if os.path.exists(index):
            os.remove(index)
    if subprocess.run(["git", "diff", "--quiet", tree, "HEAD", "--", *sorted(theirs)]).returncode != 0:
        return [], [f"撤回 PR 的内容不等于把 PR #{m.group(1)} 反向应用的结果(撤回 PR 只能撤回)"]
    return [f"撤回 PR #{m.group(1)}:{len(files)} 个文件都等于把它反向应用的结果"], []


def check_scope(base: str, branch: str) -> tuple[list[str], list[str]]:
    n, revert = issue_of(branch)
    files = changed(base)
    if revert:
        return check_revert(base, files)
    text = show("HEAD", f"docs/changes/{n}/范围.txt")
    if text is None:
        return [], [f"没有 docs/changes/{n}/范围.txt"]
    pats = [l.strip() for l in text.replace("\r\n", "\n").splitlines() if l.strip() and not l.strip().startswith("#")]
    regs = [glob_re(p) for p in pats]
    own = f"docs/changes/{n}/"
    shared = ("docs/回归清单.md", "docs/术语表.md")
    out = [f for f in files if not f.startswith((own, "docs/决策/")) and f not in shared and not any(r.match(f) for r in regs)]
    ok = [f"范围 {len(pats)} 行,改动 {len(files)} 个文件"]
    return ok, [f"范围外的改动: {f}" for f in out]


def table(text: str, first: str) -> list[dict[str, str]]:
    """Markdown 里第一列表头是 first 的那个表的行(表头 → 值)。"""
    rows, head = [], None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            head = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if head is None:
            if cells and cells[0] == first:
                head = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(dict(zip(head, cells)))
    return rows


TC = re.compile(r"TC[-_](\d+)[-_](\d+)(?!\d)")
ASSERT = re.compile(r"\bassert|\bexpect\(|\.should|\.to(?:Be|Equal|Have|Contain|Match|Throw)")


def test_files(base: str, ref: str | None = None) -> dict[str, str]:
    """[trace] test_globs 匹配的测试文件 → 内容。ref 省略时读工作区(HEAD)。"""
    cfg = tomllib.loads(show(base, "project.toml") or "")
    globs = cfg.get("trace", {}).get("test_globs", ["tests/**", "e2e/**"])
    names = git("ls-tree", "-r", "--name-only", ref).splitlines() if ref else git("ls-files").splitlines()
    out = {}
    for f in names:
        if not any(glob_re(g).match(f) or fnmatch.fnmatch(f, g) for g in globs):
            continue
        if ref:
            out[f] = show(ref, f) or ""
        else:
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    out[f] = fh.read()
            except OSError:
                pass
    return out


def tc_ids(text: str) -> set[str]:
    return {f"TC-{a}-{b}" for a, b in TC.findall(text)}


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
    这一段和 scripts/github/gates.py 里的同名函数一致:CI 把本文件拷到临时目录再跑,不能 import 兄弟文件。
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


def check_trace(base: str, branch: str) -> tuple[list[str], list[str]]:
    n, revert = issue_of(branch)
    if revert:
        return ["撤回 PR:不查需求追溯(由 scope 确认只撤回)"], []
    files = changed(base)
    if framework_only(files):
        # 框架改动没有 REQ 可追溯。这里只跳过"需求 → 用例"的追溯;
        # "已有自动用例不能消失、断言变少要提示"那部分也一并跳过 —— 框架 PR 的改动全在 CODEOWNERS 覆盖范围内,
        # 碰不到 test_globs 里的测试文件,那几条对它恒为空。
        return [f"框架 PR(只改代码负责人的文件),不查需求追溯:改动 {len(files)} 个文件"], []
    d = f"docs/changes/{n}/"
    docs = {k: show("HEAD", d + k) for k in ("01-需求.md", "03-测试用例.md", "04-证据.md")}
    if docs["01-需求.md"] is None or docs["03-测试用例.md"] is None:
        return [], [f"没有 {d}01-需求.md 或 03-测试用例.md"]
    reqs = [r["REQ 编号"] for r in table(docs["01-需求.md"], "REQ 编号") if re.fullmatch(r"REQ-\d+-\d+", r.get("REQ 编号", ""))]
    cases = [r for r in table(docs["03-测试用例.md"], "用例 ID") if re.fullmatch(r"TC-\d+-\d+", r.get("用例 ID", ""))]
    cancelled = {c["用例 ID"] for c in cases if c.get("状态") == "取消"}
    cases = [c for c in cases if c.get("状态", "有效") != "取消"]
    evidence = {r["用例 ID"]: r.get("结果", "") for r in table(docs["04-证据.md"] or "", "用例 ID")}
    ok, ng = [], []
    if not reqs:
        ng.append("01 里没有 REQ")
    for q in reqs:
        if not any(q in re.split(r"[,、\s]+", c.get("REQ", "")) for c in cases):
            ng.append(f"{q} 没有测试用例")
    head_files = test_files(base)
    tests = "\n".join(head_files.values())
    mb = git("merge-base", base, "HEAD").strip()
    base_files = test_files(base, mb)
    for tc in sorted(tc_ids("\n".join(base_files.values())) - tc_ids(tests) - cancelled):
        ng.append(f"已有的自动用例 {tc} 从测试代码里消失了(要去掉就在 03 里加这一行、状态写 取消、备注写理由)")
    for f, old in sorted(base_files.items()):
        a = len(ASSERT.findall(old))
        if f not in head_files:
            ok.append(f"注意:已有的测试文件 {f} 被删除或改名(断言 {a} 处;D3 确认理由)")
            continue
        b = len(ASSERT.findall(head_files[f]))
        if b < a:
            ok.append(f"注意:{f} 的断言从 {a} 处减到 {b} 处(D3 确认理由)")
    for c in cases:
        tc, how = c["用例 ID"], c.get("方式", "")
        for q in re.split(r"[,、\s]+", c.get("REQ", "")):
            if q and q not in reqs:
                ng.append(f"{tc} 对应的 {q} 不在 01 里")
        if how == "自动":
            if not re.search(rf"{re.escape(tc)}(?!\d)|{re.escape(tc.replace('-', '_'))}(?!\d)", tests):
                ng.append(f"{tc}(自动)在测试代码里找不到用例 ID")
        elif how == "手动":
            if evidence.get(tc) != "OK":
                ng.append(f"{tc}(手动)在 04 里没有 OK 的结果")
        else:
            ng.append(f"{tc} 的「方式」要写 自动 或 手动")
    for tc, res in evidence.items():
        if re.fullmatch(r"TC-\d+-\d+", tc) and res not in ("OK", ""):
            ng.append(f"04 里 {tc} 的结果是 {res}")
    ok.append(f"REQ {len(reqs)} 个,用例 {len(cases)} 个(自动 {sum(c.get('方式') == '自动' for c in cases)})")
    return ok, ng


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="合并前的检验")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scope", "trace"):
        p = sub.add_parser(name)
        p.add_argument("--base", required=True)
        p.add_argument("--branch", default=os.environ.get("GITHUB_HEAD_REF", ""))
    h = sub.add_parser("scope-hash"); h.add_argument("--issue", type=int, required=True); h.add_argument("--ref")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        if args.cmd == "scope-hash":
            d = f"docs/changes/{args.issue}/"

            def get(name):
                if args.ref:
                    return show(args.ref, d + name)
                if os.path.isfile(d + name):
                    with open(d + name, encoding="utf-8", newline="") as fh:
                        return fh.read()
                return None
            if get("范围.txt") is None:
                raise UsageError(f"没有 {d}范围.txt")
            print(scope_hash(get))
            return 0
        branch = args.branch or git("rev-parse", "--abbrev-ref", "HEAD").strip()
        ok, ng = (check_scope if args.cmd == "scope" else check_trace)(args.base, branch)
    except UsageError as e:
        print(f"verify: {e}", file=sys.stderr)
        return 2
    for line in ok:
        print(f"  OK  {line}")
    for line in ng:
        print(f"  NG  {line}")
    print(f"verify {args.cmd}: {'通过' if not ng else '不通过'}(NG {len(ng)})")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
