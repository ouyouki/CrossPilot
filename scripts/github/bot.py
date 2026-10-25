"""以 GitHub App 的身份运行一条 gh 或 git 命令(docs/运营规则.md 2、9 章)。bot.sh 的 Python 版。

为什么要有这一份(2026-10-25):bash 脚本在沙箱里起不来 —— MSYS2 的 bash.exe 要建命名对象,被沙箱拒绝
(NtCreateDirectoryObject(\\BaseNamedObjects\\msys-2.0...) 0xC0000022);openssl 不在 PATH;gh 也没装。
于是"推一次代码"变成"要人盯着屏幕点一次全权限",而 Agent 会退回到人的 SSH 身份去推 —— 这违反
"Agent 不用人的身份"。这一份不依赖 bash、openssl、curl、gh:JWT 用纯 Python 签(RS256),API 用 urllib,
令牌通过 GIT_CONFIG_VALUE 交给 git,不进命令行。

允许清单和 bot.sh 完全一致(两边一起改;最终是让 bot.sh 变成调用本文件的包装)。

    python scripts/github/bot.py <dev|pm|review> gh <组> <动作> [参数...]
    python scripts/github/bot.py <dev|pm|review> git fetch [origin] [--tags] [--prune]
    python scripts/github/bot.py <dev|pm|review> git push [-u] origin <feat|fix>/<编号>-<短名>

gh 的每组命令翻译成 GitHub REST API,输出是 JSON(键名和 API 一致,不模拟 gh 的表格输出)。
环境变量 BOT_ROLE、BOT_CONFIG_DIR、BOT_DRY_RUN 和 bot.sh 一样。
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROLES = ("dev", "pm", "review")
HUMAN_LABELS = ("设计已批准", "已验收", "免验收")
REVIEW_LABELS = r"^(状态:方案中|状态:待定版|待回答|待人决定|阻塞|需人定版)$"
BRANCH = re.compile(r"^(feat|fix)/[0-9]+-[a-z0-9][a-z0-9-]*$")
GH_READ = {("issue", "view"), ("issue", "list"), ("issue", "comment"), ("pr", "view"), ("pr", "list"),
           ("pr", "diff"), ("pr", "checks"), ("pr", "comment"), ("label", "list"), ("search", "issues"),
           ("search", "prs"), ("release", "view"), ("release", "list"), ("run", "view"), ("run", "list")}
MILESTONES = re.compile(r"^/?repos/([^/]+)/([^/]+)/milestones(/[0-9]+)?$")


class Refuse(Exception):
    """按规则不做。退出码 2(和 bot.sh 一样)。"""


# ---- 读参数 -----------------------------------------------------------------------------------------------------------------
def parse(args: list[str], value_flags: set[str]) -> tuple[dict[str, list[str | None]], list[str]]:
    """拆成"带值的选项 / 不带值的选项 / 位置参数"。--x=y 和 --x y 两种写法都认。"""
    flags: dict[str, list[str | None]] = {}
    pos, i = [], 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and "=" in a:
            k, _, v = a.partition("=")
            flags.setdefault(k, []).append(v)
        elif a in value_flags:
            if i + 1 >= len(args):
                raise Refuse(f"{a} 后面要有值")
            flags.setdefault(a, []).append(args[i + 1])
            i += 1
        elif a.startswith("-") and a != "-":
            flags.setdefault(a, []).append(None)
        else:
            pos.append(a)
        i += 1
    return flags, pos


def fget(flags: dict[str, list[str | None]], *names: str) -> str | None:
    for n in names:
        vals = [v for v in flags.get(n, []) if v is not None]
        if vals:
            return vals[-1]
    return None


def fget_all(flags: dict[str, list[str | None]], *names: str) -> list[str]:
    out = []
    for n in names:
        out += [v for v in flags.get(n, []) if v is not None]
    return out


def body_of(flags: dict[str, list[str | None]], required: bool = False) -> str:
    b = fget(flags, "--body", "-b")
    if b is not None:
        return b
    bf = fget(flags, "--body-file", "-F")
    if bf is not None:
        return sys.stdin.read() if bf == "-" else _read(bf)
    if required:
        raise Refuse("要写 --body 或 --body-file(评论、Issue、PR 的正文)")
    return ""


# ---- 仓库与设置 -------------------------------------------------------------------------------------------------------------
def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def repo_root() -> str:
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8")
    return (p.stdout or "").strip() or os.getcwd()


def project(root: str) -> dict[str, str]:
    import tomllib
    with open(os.path.join(root, "project.toml"), "rb") as f:
        gh = tomllib.load(f).get("github", {})
    owner, repo = gh.get("owner", ""), gh.get("repo", "")
    if not owner or not repo:
        raise Refuse("project.toml 的 [github] 缺 owner / repo")
    if len({gh.get("dev_bot"), gh.get("pm_bot"), gh.get("review_bot")}) != 3:
        raise Refuse("dev_bot、pm_bot、review_bot 要是三个不同的 App(做的和审的必须分开)")
    return {"owner": owner, "repo": repo}


def load_env_file(path: str) -> dict[str, str]:
    """读 <role>.env。格式和 bot.sh 一样:KEY=VALUE,容忍 CRLF 和两边的引号。"""
    out: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            k, sep, v = line.strip("\r\n").partition("=")
            if not sep:
                continue
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


# ---- RS256(纯 Python,不依赖 openssl)--------------------------------------------------------------------------------------
def _tlv(data: bytes, off: int) -> tuple[int, bytes, int]:
    tag = data[off]
    off += 1
    ln = data[off]
    off += 1
    if ln & 0x80:
        n = ln & 0x7F
        ln = int.from_bytes(data[off:off + n], "big")
        off += n
    return tag, data[off:off + ln], off + ln


def _items(data: bytes) -> list[tuple[int, bytes]]:
    out, off = [], 0
    while off < len(data):
        tag, val, off = _tlv(data, off)
        out.append((tag, val))
    return out


def _pem_der(path: str) -> bytes:
    text = _read(path)
    m = re.search(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----(.*?)-----END", text, re.S)
    if not m:
        raise Refuse(f"{path} 里没有 PRIVATE KEY(App 的私钥 .pem)")
    return base64.b64decode("".join(m.group(1).split()))


def rsa_key(path: str) -> tuple[int, int]:
    """从 PEM 里取出 (n, d)。GitHub App 的私钥可能是 PKCS#1 或 PKCS#8,两种都认。"""
    der = _pem_der(path)
    top = _items(der)[0][1]
    items = _items(top)
    if len(items) >= 3 and items[1][0] == 0x30:                      # PKCS#8: 第二项是算法,私钥在 OCTET STRING 里
        top = _items(items[2][1])[0][1]
        items = _items(top)
    if len(items) < 4:
        raise Refuse(f"{path} 不是 RSA 私钥")
    n = int.from_bytes(items[1][1], "big")
    d = int.from_bytes(items[3][1], "big")
    return n, d


def sign_rs256(key_path: str, message: bytes) -> bytes:
    """RSASSA-PKCS1-v1_5 + SHA-256。签名的长度必须正好是模长,GitHub 才认。"""
    n, d = rsa_key(key_path)
    k = (n.bit_length() + 7) // 8
    digest_info = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(message).digest()
    if k < len(digest_info) + 11:
        raise Refuse("私钥太短(至少 2048 位)")
    em = b"\x00\x01" + b"\xff" * (k - len(digest_info) - 3) + b"\x00" + digest_info
    return pow(int.from_bytes(em, "big"), d, n).to_bytes(k, "big")


def make_jwt(app_id: str, key_path: str) -> str:
    def b64u(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    now = int(time.time())
    head = b64u(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = b64u(json.dumps({"iat": now - 60, "exp": now + 540, "iss": app_id},
                             separators=(",", ":")).encode())
    signing_input = f"{head}.{claims}"
    return f"{signing_input}.{b64u(sign_rs256(key_path, signing_input.encode()))}"


# ---- HTTP -------------------------------------------------------------------------------------------------------------------
def api_call(method: str, path: str, token: str, body: dict | None = None,
             accept: str = "application/vnd.github+json") -> tuple[int, bytes, dict]:
    url = "https://api.github.com" + (path if path.startswith("/") else "/" + path)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "crosspilot-bot")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except urllib.error.URLError as e:
        raise Refuse(f"连不上 GitHub({e.reason})。这条命令没有发出去。")


def api_json(method: str, path: str, token: str, body: dict | None = None,
             accept: str = "application/vnd.github+json"):
    status, raw, _ = api_call(method, path, token, body, accept)
    if status >= 400:
        try:
            msg = json.loads(raw).get("message", "")
        except (ValueError, AttributeError):
            msg = raw[:300].decode("utf-8", "replace")
        raise Refuse(f"GitHub 返回 {status}:{msg or '(没有说明)'}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", "replace")


# ---- 隔离检查(docs/运营规则.md 9 章)-----------------------------------------------------------------------------------------
def assert_isolation() -> None:
    """Agent 的环境里不能有人的 GitHub 凭据。只查 gh 和 https 凭据,SSH 私钥查不了 —— 那个靠系统用户隔离。"""
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        raise Refuse("环境变量 GH_TOKEN / GITHUB_TOKEN 有值:Agent 的环境里不放令牌")
    try:
        p = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=20)
        if p.returncode == 0 and p.stdout.strip():
            raise Refuse("这个环境里有人的 gh 登录。Agent 要在没有人的 GitHub 凭据的环境"
                         "(另一个系统用户或容器)里运行(引导手册 4 步)")
    except FileNotFoundError:
        pass                                            # 没装 gh 就没有 gh 的登录
    p = subprocess.run(["git", "-c", "credential.interactive=never", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True, timeout=30)
    if re.search(r"^password=", p.stdout or "", re.M):
        raise Refuse("这个环境里有人的 git 凭据(github.com)。Agent 要在没有人的 GitHub 凭据的环境里运行")


# ---- 允许清单(和 bot.sh 一致)----------------------------------------------------------------------------------------------
def labels_ok(role: str, only: str | None, args: list[str]) -> None:
    prev = ""
    for a in args:
        op, val = "", ""
        if prev in ("--add-label", "--remove-label", "--label", "-l"):
            op, val = prev, a
        elif re.fullmatch(r"-l.+", a):
            op, val = "--label", a[2:]
        elif re.fullmatch(r"--(add|remove)-label=.+", a) or a.startswith("--label="):
            op, _, val = a.partition("=")
        if op:
            for lab in (x.strip() for x in val.split(",")):
                if lab in HUMAN_LABELS:
                    raise Refuse(f"人专用标签({lab})只由人加或去掉")
                if op == "--remove-label" and lab == "需人定版":
                    raise Refuse("需人定版 只由人去掉")
                if only and not re.fullmatch(only, lab):
                    raise Refuse(f"身份 {role} 不能改标签 {lab}")
        elif only and a.startswith("-") and a not in ("--add-label", "--remove-label"):
            raise Refuse(f"身份 {role} 用 gh issue edit 只能改标签")
        prev = a


def check_gh(role: str, group: str, action: str, rest: list[str]) -> None:
    pair = (group, action)
    if pair in GH_READ:
        return
    if pair in (("issue", "close"), ("issue", "reopen")):
        if role != "dev":
            raise Refuse(f"身份 {role} 不能 {action} Issue")
        return
    if pair in (("pr", "create"), ("pr", "edit")):
        if role != "dev":
            raise Refuse("只有开发 App(开发、集成 Agent)能开或改 PR")
        labels_ok(role, None, rest)
        return
    if pair == ("issue", "create"):
        labels_ok(role, None, rest)
        if role == "review":                            # /architecture 专用:标签正好是这两个
            got = set()
            prev = ""
            for a in rest:
                val = ""
                if prev in ("--label", "-l"):
                    val = a
                elif re.fullmatch(r"(--label=|-l)(.+)", a):
                    val = re.fullmatch(r"(--label=|-l)(.+)", a).group(2)
                if val:
                    got |= {x.strip() for x in val.split(",")}
                prev = a
            if not {"类型:改进", "需人定版"} <= got:
                raise Refuse("评审 App 建的 Issue 要带 类型:改进 和 需人定版")
            if got - {"类型:改进", "需人定版"}:
                raise Refuse("评审 App 建的 Issue 只能带 类型:改进、需人定版")
        return
    if pair == ("issue", "edit"):
        labels_ok(role, REVIEW_LABELS if role == "review" else None, rest)
        return
    if pair == ("pr", "merge"):
        if role != "dev":
            raise Refuse("只有开发 App(集成 Agent)能合并")
        squash = False
        for a in rest:
            if a in ("--squash", "-s"):
                squash = True
            elif a in ("--admin", "--auto", "--merge", "-m", "--rebase", "-r", "--disable-auto"):
                raise Refuse(f"合并只用 --squash(不许 {a})")
        if not squash:
            raise Refuse("合并要写 --squash")
        return
    if pair == ("pr", "review"):
        if role == "dev":
            raise Refuse("开发 App 不评审")
        if role == "pm":
            for a in rest:
                if re.fullmatch(r"(--approve|-a|--request-changes|-r)(=.*)?", a):
                    raise Refuse("PM App 只写评论型的评审(--comment)")
        return
    if group == "api":
        method = api_method(rest)
        if method == "GET":
            return
        path = action
        if role == "dev" and MILESTONES.match(path):
            return
        raise Refuse("gh api 的写操作(只允许开发 App 经 bot.py 写里程碑)")
    raise Refuse(f"不允许的操作: gh {group} {action}(身份 {role})。见 bot.py 开头的允许清单")


def api_method(rest: list[str]) -> str:
    nx = [a for a in rest if re.fullmatch(r"(-X|--method)(=.*)?", a)]
    if len(nx) > 1:
        raise Refuse("gh api 的 -X / --method 只能写一次")
    m = re.fullmatch(r"(-X|--method)(?:=|\s)?([A-Za-z]+)", " ".join(rest))
    if m:
        return m.group(2).upper()
    if any(a in ("-f", "-F", "--field", "--raw-field", "--input") or a.startswith(("-f", "-F", "--field=", "--raw-field=", "--input="))
           for a in rest):
        return "POST"
    return "GET"


def check_git(role: str, sub: str, args: list[str]) -> None:
    if sub == "fetch":
        for a in args:
            if a not in ("origin", "--tags", "--prune", "-q", "--quiet"):
                raise Refuse("git fetch 只允许 origin、--tags、--prune")
        return
    if sub == "push":
        if role == "review":
            raise Refuse("评审 App 不推送")
        n = 0
        for a in args:
            if a in ("-u", "--set-upstream", "origin"):
                continue
            if not BRANCH.match(a):
                raise Refuse(f"只能推送功能分支 feat|fix/<编号>-<短名>(收到: {a})")
            n += 1
        if n != 1:
            raise Refuse("git push 要写一个功能分支")
        return
    raise Refuse("git 只允许 fetch 和 push")


# ---- 令牌 -------------------------------------------------------------------------------------------------------------------
PERMS = {"review": {"contents": "read", "issues": "write", "pull_requests": "write", "metadata": "read"}}
DEFAULT_PERMS = {"contents": "write", "issues": "write", "pull_requests": "write", "metadata": "read"}


def token_for(role: str, gh: dict[str, str], cfg_path: str) -> str:
    cfg = load_env_file(cfg_path)
    broker = cfg.get("BROKER_URL", "")
    if broker:
        if cfg.get("PRIVATE_KEY_FILE"):
            raise Refuse(f"用令牌代理时,{cfg_path} 里不写 PRIVATE_KEY_FILE(私钥只放在代理那边)")
        if not re.fullmatch(r"http://(127\.0\.0\.1|localhost):[0-9]+", broker):
            raise Refuse("BROKER_URL 只能是 http://127.0.0.1:<端口>(口令不发到本机以外)")
        secret_file = cfg.get("BROKER_SECRET_FILE", "")
        if not os.path.isfile(secret_file):
            raise Refuse(f"找不到 BROKER_SECRET_FILE({secret_file})")
        req = urllib.request.Request(f"{broker}/token/{role}")
        req.add_header("Authorization", "Bearer " + _read(secret_file).strip())
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.load(r)
        except urllib.error.URLError as e:
            raise Refuse(f"连不上令牌代理 {broker}(代理在运行吗? {e.reason})")
        if not resp.get("token"):
            raise Refuse(f"令牌代理没给令牌:{resp.get('message', '未知的错误')}")
        return resp["token"]

    app_id, iid, key = cfg.get("APP_ID", ""), cfg.get("INSTALLATION_ID", ""), cfg.get("PRIVATE_KEY_FILE", "")
    if not (app_id.isdigit() and iid.isdigit() and os.path.isfile(key)):
        raise Refuse(f"{cfg_path} 里 APP_ID / INSTALLATION_ID 要是数字,PRIVATE_KEY_FILE 要指向存在的文件"
                     "(或改用令牌代理:BROKER_URL、BROKER_SECRET_FILE)")
    jwt = make_jwt(app_id, key)
    if os.environ.get("BOT_DRY_RUN") == "1":
        n, _ = rsa_key(key)
        print(f"bot.py: JWT 已签(RSA {n.bit_length()} 位,App {app_id},安装 {iid})。dry-run:不连 GitHub,不运行。")
        sys.exit(0)
    body = {"repositories": [gh["repo"]], "permissions": PERMS.get(role, DEFAULT_PERMS)}
    status, raw, _ = api_call("POST", f"/app/installations/{iid}/access_tokens", jwt, body)
    if status >= 400:
        try:
            msg = json.loads(raw).get("message", "")
        except (ValueError, AttributeError):
            msg = raw[:300].decode("utf-8", "replace")
        raise Refuse(f"没拿到安装令牌:{msg or '(没有说明)'}(检查 App 的 ID、安装 ID、权限、电脑的时间)")
    token = json.loads(raw).get("token", "")
    if not token:
        raise Refuse("没拿到安装令牌(GitHub 的响应里没有 token)")
    return token


# ---- gh 的实现(翻译成 REST)-------------------------------------------------------------------------------------------------
def out(obj) -> None:
    if isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def run_gh(role: str, group: str, action: str, rest: list[str], tok: str, gh: dict[str, str]) -> None:
    o, r = gh["owner"], gh["repo"]
    base = f"/repos/{o}/{r}"
    if group == "api":
        return run_api(role, action, rest, tok)
    if group == "issue":
        return run_issue(action, rest, tok, base)
    if group == "pr":
        return run_pr(action, rest, tok, base)
    if group == "label" and action == "list":
        return out(api_json("GET", f"{base}/labels?per_page=100", tok))
    if group == "search":
        q = fget(parse(rest, {"--limit", "-L", "--repo", "-R", "--state"})[0], "--limit", "-L") or "30"
        terms = " ".join(parse(rest, {"--limit", "-L", "--repo", "-R", "--state"})[1])
        kind = "is:issue" if action == "issues" else "is:pr"
        query = urllib.parse.quote_plus(f"repo:{o}/{r} {kind} {terms}")
        return out(api_json("GET", f"/search/issues?q={query}&per_page={q}", tok))
    if group == "release":
        if action == "list":
            return out(api_json("GET", f"{base}/releases?per_page=100", tok))
        num = _tag_or_num(rest)
        return out(api_json("GET", f"{base}/releases/tags/{num}", tok))
    if group == "run":
        if action == "list":
            return out(api_json("GET", f"{base}/actions/runs?per_page=30", tok))
        rid = _first_num(rest, "run view 要写运行 ID")
        return out(api_json("GET", f"{base}/actions/runs/{rid}", tok))
    raise Refuse(f"还没实现: gh {group} {action}")


def _first_num(rest: list[str], why: str) -> str:
    for a in rest:
        if a.isdigit():
            return a
    raise Refuse(why)


def _tag_or_num(rest: list[str]) -> str:
    for a in rest:
        if not a.startswith("-"):
            return a
    raise Refuse("要写 Release 的 tag")


def run_api(role: str, path: str, rest: list[str], tok: str) -> None:
    flags, _ = parse(rest, {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input", "-H"})
    method = fget(flags, "-X", "--method") or ("POST" if any(flags.get(k) for k in
                                                             ("-f", "-F", "--field", "--raw-field", "--input")) else "GET")
    body = None
    for k in ("-f", "--field", "--raw-field", "-F"):
        for v in flags.get(k, []):
            if v:
                key, _, val = v.partition("=")
                body = body or {}
                body[key] = val
    inp = fget(flags, "--input")
    if inp:
        body = json.loads(_read(inp))
    status, raw, _ = api_call(method.upper(), path, tok, body)
    text = raw.decode("utf-8", "replace") if raw else ""
    try:
        out(json.loads(text)) if text else None
    except ValueError:
        out(text)
    if status >= 400:
        raise Refuse(f"GitHub 返回 {status}")


def run_issue(action: str, rest: list[str], tok: str, base: str) -> None:
    vf = {"--title", "-t", "--body", "-b", "--body-file", "-F", "--label", "-l", "--add-label",
          "--remove-label", "--state", "-s", "--limit", "-L", "--search", "--assignee", "-a", "--milestone", "-m"}
    flags, pos = parse(rest, vf)
    if action == "view":
        return out(api_json("GET", f"{base}/issues/{_first_num(pos, 'issue view 要写编号')}", tok))
    if action == "list":
        n = fget(flags, "--limit", "-L") or "30"
        state = fget(flags, "--state", "-s") or "open"
        q = f"?state={state}&per_page={n}"
        labels = fget_all(flags, "--label", "-l")
        if labels:
            q += "&labels=" + urllib.parse.quote(",".join(labels))
        if fget(flags, "--search"):
            q += "&q=" + urllib.parse.quote(fget(flags, "--search"))
        items = api_json("GET", f"{base}/issues{q}", tok)
        return out([x for x in items if "pull_request" not in x])
    if action == "create":
        title = fget(flags, "--title", "-t")
        if not title:
            raise Refuse("issue create 要写 --title")
        body = {"title": title, "body": body_of(flags)}
        labels = [x for v in fget_all(flags, "--label", "-l") for x in v.split(",") if x.strip()]
        if labels:
            body["labels"] = labels
        return out(api_json("POST", f"{base}/issues", tok, body))
    if action == "comment":
        num = _first_num(pos, "issue comment 要写编号")
        return out(api_json("POST", f"{base}/issues/{num}/comments", tok, {"body": body_of(flags, True)}))
    if action in ("close", "reopen"):
        num = _first_num(pos, f"issue {action} 要写编号")
        return out(api_json("PATCH", f"{base}/issues/{num}",
                            tok, {"state": "closed" if action == "close" else "open"}))
    if action == "edit":
        num = _first_num(pos, "issue edit 要写编号")
        patch: dict = {}
        if fget(flags, "--title", "-t"):
            patch["title"] = fget(flags, "--title", "-t")
        if fget(flags, "--body", "-b") is not None or fget(flags, "--body-file", "-F") is not None:
            patch["body"] = body_of(flags)
        add = [x for v in fget_all(flags, "--add-label") for x in v.split(",") if x.strip()]
        rem = [x for v in fget_all(flags, "--remove-label") for x in v.split(",") if x.strip()]
        if add or rem:
            cur = api_json("GET", f"{base}/issues/{num}/labels?per_page=100", tok)
            names = [x["name"] for x in cur]
            patch["labels"] = [x for x in names if x not in rem] + [x for x in add if x not in names]
        return out(api_json("PATCH", f"{base}/issues/{num}", tok, patch))
    raise Refuse(f"还没实现: gh issue {action}")


def run_pr(action: str, rest: list[str], tok: str, base: str) -> None:
    vf = {"--title", "-t", "--body", "-b", "--body-file", "-F", "--base", "-B", "--head", "-H",
          "--state", "-s", "--limit", "-L", "--label", "-l", "--add-label", "--remove-label", "--search"}
    flags, pos = parse(rest, vf)
    if action in ("view", "diff", "checks"):
        num = _first_num(pos, f"pr {action} 要写 PR 编号")
        if action == "diff":
            status, raw, _ = api_call("GET", f"{base}/pulls/{num}", tok, accept="application/vnd.github.v3.diff")
            if status >= 400:
                raise Refuse(f"GitHub 返回 {status}")
            return out(raw.decode("utf-8", "replace"))
        pr = api_json("GET", f"{base}/pulls/{num}", tok)
        if action == "view":
            return out(pr)
        sha = pr["head"]["sha"]
        runs = api_json("GET", f"{base}/commits/{sha}/check-runs", tok)
        return out([{"name": c["name"], "status": c["status"], "conclusion": c["conclusion"]}
                    for c in runs.get("check_runs", [])])
    if action == "list":
        n = fget(flags, "--limit", "-L") or "30"
        state = fget(flags, "--state", "-s") or "open"
        return out(api_json("GET", f"{base}/pulls?state={state}&per_page={n}", tok))
    if action == "create":
        for k, name in (("--title", "-t"), ("--head", "-H"), ("--base", "-B")):
            if not fget(flags, k, name):
                raise Refuse(f"pr create 要写 {k}")
        body = {"title": fget(flags, "--title", "-t"), "head": fget(flags, "--head", "-H"),
                "base": fget(flags, "--base", "-B"), "body": body_of(flags)}
        return out(api_json("POST", f"{base}/pulls", tok, body))
    if action == "edit":
        num = _first_num(pos, "pr edit 要写 PR 编号")
        patch = {}
        if fget(flags, "--title", "-t"):
            patch["title"] = fget(flags, "--title", "-t")
        if fget(flags, "--body", "-b") is not None or fget(flags, "--body-file", "-F") is not None:
            patch["body"] = body_of(flags)
        return out(api_json("PATCH", f"{base}/pulls/{num}", tok, patch))
    if action == "comment":
        num = _first_num(pos, "pr comment 要写 PR 编号")
        return out(api_json("POST", f"{base}/issues/{num}/comments", tok, {"body": body_of(flags, True)}))
    if action == "merge":
        num = _first_num(pos, "pr merge 要写 PR 编号")
        return out(api_json("PUT", f"{base}/pulls/{num}/merge", tok, {"merge_method": "squash"}))
    if action == "review":
        num = _first_num(pos, "pr review 要写 PR 编号")
        event = "COMMENT"                                # --approve / -r 不带值,所以看"有没有这个选项"
        if "-a" in flags or "--approve" in flags:
            event = "APPROVE"
        elif "-r" in flags or "--request-changes" in flags:
            event = "REQUEST_CHANGES"
        return out(api_json("POST", f"{base}/pulls/{num}/reviews", tok,
                            {"event": event, "body": body_of(flags)}))
    raise Refuse(f"还没实现: gh pr {action}")


# ---- git --------------------------------------------------------------------------------------------------------------------
def run_git(sub: str, args: list[str], tok: str) -> int:
    b64 = base64.b64encode(f"x-access-token:{tok}".encode()).decode()
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0",
           # 令牌放在 GIT_CONFIG_VALUE 里(环境变量),不进命令行 —— 命令行会被 ps 看到
           "GIT_CONFIG_COUNT": "4",
           "GIT_CONFIG_KEY_0": "credential.helper", "GIT_CONFIG_VALUE_0": "",
           "GIT_CONFIG_KEY_1": "url.https://github.com/.insteadOf", "GIT_CONFIG_VALUE_1": "git@github.com:",
           "GIT_CONFIG_KEY_2": "url.https://github.com/.insteadOf", "GIT_CONFIG_VALUE_2": "ssh://git@github.com/",
           "GIT_CONFIG_KEY_3": "http.https://github.com/.extraheader",
           "GIT_CONFIG_VALUE_3": f"AUTHORIZATION: basic {b64}"}
    env.pop("BOT_TOKEN", None)
    p = subprocess.run(["git", sub, *args], cwd=repo_root(), env=env)
    return p.returncode


# ---- 入口 -------------------------------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    if len(argv) < 2:
        print("用法: python scripts/github/bot.py <dev|pm|review> gh|git <参数...>", file=sys.stderr)
        return 2
    role, rest = argv[0], argv[1:]
    try:
        if role not in ROLES:
            raise Refuse("身份只能是 dev、pm 或 review")
        if os.environ.get("BOT_ROLE") != role:
            raise Refuse(f"这个环境的 BOT_ROLE 是 {os.environ.get('BOT_ROLE') or '(没设)'},"
                         f"不能用 {role} 的身份(一个环境只用一个身份)")
        assert_isolation()
        root = repo_root()
        gh = project(root)
        top = rest[0]
        if top == "gh":
            if len(rest) < 3:
                raise Refuse("要写 gh <组> <动作>")
            group, action, args = rest[1], rest[2], rest[3:]
            if group.startswith("-") or action.startswith("-"):
                raise Refuse("把选项放在 gh <组> <动作> 后面")
            check_gh(role, group, action, args)
            cfg_dir = os.environ.get("BOT_CONFIG_DIR") or os.path.join(
                os.path.expanduser("~"), ".github-bots", f"{gh['owner']}-{gh['repo']}")
            cfg_path = os.path.join(cfg_dir, f"{role}.env")
            if not os.path.isfile(cfg_path):
                raise Refuse(f"找不到 {cfg_path}(引导手册 4 步)")
            tok = token_for(role, gh, cfg_path)
            run_gh(role, group, action, args, tok, gh)
            return 0
        if top == "git":
            if len(rest) < 2:
                raise Refuse("要写 git fetch 或 git push")
            sub, args = rest[1], rest[2:]
            check_git(role, sub, args)
            cfg_dir = os.environ.get("BOT_CONFIG_DIR") or os.path.join(
                os.path.expanduser("~"), ".github-bots", f"{gh['owner']}-{gh['repo']}")
            cfg_path = os.path.join(cfg_dir, f"{role}.env")
            if not os.path.isfile(cfg_path):
                raise Refuse(f"找不到 {cfg_path}(引导手册 4 步)")
            tok = token_for(role, gh, cfg_path)
            return run_git(sub, args, tok)
        raise Refuse(f"只能代理 gh 和 git(收到: {top})")
    except Refuse as e:
        print(f"bot.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
