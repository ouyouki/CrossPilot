"""命令监视(docs/运营规则.md 9 章)。Claude Code 的 PreToolUse hook 和 OpenCode 的插件都调用它。

从标准输入读工具调用的 JSON({"tool_input": {"command": "..."}}),要拦的命令以退出码 2 结束并在标准错误写理由,其他退出码 0。
读不懂输入时也拦(退出码 2)。拦的东西:
  * 改写或删除共享的历史: git push 的强推 / 删除 / 跳过 hook,推送 main;git rebase、reset --hard、clean、checkout -- <路径>、
    restore(--staged 以外)、branch -D / -d -f、tag -d;跳过检查: --no-verify、commit -n、core.hooksPath;
  * 读密钥: cat / type / less / more / head / tail / grep / findstr / sed / awk / Get-Content 等读 .env、*.pem、*.key、id_rsa* 等;
    显示环境变量(printenv、env、set、Get-ChildItem env:)或引用 ANTHROPIC_AUTH_TOKEN、DEEPSEEK_API_KEY、GH_TOKEN 等;
  * 系统能力(一次就回不来,所以不是问人,是做不到): 改账户或密码(net user / net localgroup / Set-LocalUser 等)、写注册表、
    装或改系统服务、建或改计划任务、改文件权限或所有者(icacls / takeown)、动磁盘和启动项、改执行策略、
    动防火墙和防御设置、动凭据库、提权(runas / sudo)、看不出会执行什么的启动器(rundll32 / wmic / mshta 等)、动 SSH 密钥。
    为什么单独成一层:Agent 和人在同一个系统用户下运行时,它改得动人的登录密码(2026-10 发生过,人登不进去);
    根上的解法是分开身份(docs/运营规则.md 9 章),这一层负责不给它这个机会;
  * GitHub: 不经 scripts/github/bot.sh 的 gh 写操作和 git push(Agent 不用人的身份);无论经不经 bot.sh 都不许的:
    触发工作流、操作 Release、写标签或 refs、加或去掉人专用标签、去掉 需人定版;
    合并 PR 只许 bot.sh dev 的 gh pr merge --squash;批准或要求修改只许 bot.sh review 的 gh pr review(PM 只写 --comment)。
  * 上网: curl / wget / Invoke-WebRequest 等只许访问本机(localhost)和 project.toml 的 [runner] web_domains(含子域名);看不出访问哪里的也拦。
bash -c / bash -lc / sh -c / powershell -Command 里的命令也会再判断;VAR=值、env、command、& / . / call、行首的 ( { 会被跳过。
heredoc 的正文(<<'EOF' … EOF 之间)是写进评论的文字,不当作命令判断。
这是防误操作,不是权限的边界:边界是 GitHub 的规则集和 CI,以及"Agent 的运行环境里没有人的 GitHub 凭据"(bot.sh 会检查)。
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

SEGMENT = re.compile(r"&&|\|\||[;|\n]")
READERS = {"cat", "type", "less", "more", "head", "tail", "get-content", "gc", "bat", "strings", "xxd", "od", "base64", "cp", "copy",
           "select-string", "sls", "grep", "egrep", "rg", "findstr", "sed", "awk", "nl", "tac"}
SHELLS = {"bash", "sh", "zsh", "dash", "powershell", "pwsh", "cmd", "powershell.exe", "pwsh.exe", "cmd.exe"}
GIT_OPTS_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
GH_OPTS_WITH_ARG = {"-R", "--repo", "--hostname"}
PUSH_BAD = {"--force", "-f", "--force-if-includes", "--no-verify", "--mirror", "--delete", "-d", "--prune"}
HUMAN_LABELS = ("设计已批准", "已验收", "免验收")
SECRET_VARS = re.compile(r"ANTHROPIC_AUTH_TOKEN|ANTHROPIC_API_KEY|DEEPSEEK_API_KEY|GH_TOKEN|GITHUB_TOKEN|BOT_TOKEN|OPENAI_API_KEY")
GH_READ = {("issue", "view"), ("issue", "list"), ("issue", "status"), ("pr", "view"), ("pr", "list"), ("pr", "diff"), ("pr", "checks"),
           ("pr", "status"), ("run", "view"), ("run", "list"), ("release", "view"), ("release", "list"), ("label", "list"),
           ("repo", "view"), ("auth", "status"), ("workflow", "list"), ("workflow", "view"), ("search", "issues"), ("search", "prs")}
BOT = "scripts/github/bot.sh"
NET = {"curl", "wget", "invoke-webrequest", "iwr", "invoke-restmethod", "irm", "curl.exe", "wget.exe"}
HOST = re.compile(r"^(?:https?://)?(?:[^/@\s]*@)?(localhost|[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)(?::\d+)?(?:[/?#]|$)")
LOCAL = ("localhost", "127.0.0.1")                     # 测试时访问本机起的应用

# 系统能力要用的名字。这一类的共同点是一次就回不来,所以拦,而不只是提醒(理由见文件开头的说明)。
ACCOUNT_SUB = {"user", "localgroup", "group", "accounts"}
ACCOUNT_HEADS = {"chntpw", "passwd", "chpasswd", "usermod", "useradd", "userdel", "adduser", "deluser",
                 "addgroup", "delgroup", "dsmod", "dsadd", "dsrm", "net1"}
ACCOUNT_PS = {"new-localuser", "set-localuser", "remove-localuser", "rename-localuser", "add-localgroupmember",
              "remove-localgroupmember", "new-localgroup", "remove-localgroup", "set-localgroup"}
REG_WRITE = {"add", "delete", "import", "load", "unload", "copy", "restore", "save"}
REG_PS = {"new-itemproperty", "set-itemproperty", "remove-itemproperty", "rename-itemproperty",
          "new-item", "set-item", "remove-item"}
REG_PATH = re.compile(r"(?i)hk(lm|cu|cr|ey|u|cc):|hkey_|\\\\registry\\\\")
SERVICE_SUB = {"create", "delete", "config", "description", "failure", "sdset", "triggerinfo"}
SERVICE_HEADS = {"new-service", "set-service", "remove-service"}
TASK_SUB = {"/create", "/delete", "/change", "/run", "/end"}
TASK_HEADS = {"register-scheduledtask", "unregister-scheduledtask", "set-scheduledtask", "new-scheduledtask",
              "disable-scheduledtask", "enable-scheduledtask"}
ACL_FLAG = ("/grant", "/deny", "/remove", "/setowner", "/reset", "/inheritance", "/g", "/p", "/r", "/d", "/e")
DISK_HEADS = {"diskpart", "format", "bcdedit", "bootrec", "fdisk", "mkfs", "clear-disk", "initialize-disk",
              "format-volume", "remove-partition", "set-partition", "new-partition"}
FIREWALL_HEADS = {"set-mppreference", "add-mppreference", "remove-mppreference", "set-netfirewallprofile",
                  "new-netfirewallrule", "remove-netfirewallrule", "set-netfirewallrule", "disable-netfirewallprofile"}
VAULT_HEADS = {"cmdkey", "vaultcmd", "get-storedcredential"}
# 看不出会执行什么的启动器:用来绕开别的检查最常见的载体,PM Agent 没有正当用途
OPAQUE_HEADS = {"rundll32", "regsvr32", "mshta", "wscript", "cscript", "certutil", "bitsadmin", "wmic", "regedit"}


def web_domains() -> list[str]:
    try:
        rc = tomllib.loads((Path(__file__).resolve().parents[2] / "project.toml").read_text(encoding="utf-8")).get("runner", {})
        return [d.lower() for d in rc.get("web_domains", []) if isinstance(d, str)]
    except (OSError, tomllib.TOMLDecodeError):
        return []


# 选项后面跟着的值:URL 类要检查,其余(输出文件、数据、头)跳过。按命令分开(curl 的 -O 不带值,wget 的 -O 带)
URL_OPTS = {"--url", "-x", "--proxy", "-uri", "-proxy", "-e"}
VALUE_OPTS = {
    "curl": {"-o", "--output", "-d", "--data", "--data-raw", "--data-binary", "--data-urlencode", "--json", "-H", "--header", "-u", "--user",
             "-A", "--user-agent", "--referer", "-X", "--request", "-T", "--upload-file", "-F", "--form", "-w", "--write-out",
             "-b", "--cookie", "-c", "--cookie-jar", "-m", "--max-time", "--connect-timeout", "--retry", "-K", "--config", "-r", "--range"},
    "wget": {"-O", "--output-document", "-o", "--output-file", "-a", "--append-output", "-P", "--directory-prefix", "--header",
             "--post-data", "--post-file", "--user", "--password", "-U", "--user-agent", "-t", "--tries", "-T", "--timeout"},
    "iwr": {"-outfile", "-method", "-body", "-headers", "-contenttype", "-infile", "-timeoutsec", "-useragent"},
}


def _net_reason(tokens: list[str]) -> str:
    name = tokens[0].lower().removesuffix(".exe")
    kind = name if name in ("curl", "wget") else "iwr"
    skip, check = VALUE_OPTS[kind], {o for o in URL_OPTS if not (kind == "curl" and o == "-e")}  # curl -e = referer
    hosts, i = [], 1
    while i < len(tokens):
        t = tokens[i]
        low = t.lower() if kind == "iwr" else t
        opt, eq, val = low.partition("=")
        if t.startswith("-"):
            if eq and opt in check:
                cand = [val]
            elif low in check and i + 1 < len(tokens):
                cand, i = [tokens[i + 1]], i + 1
            else:
                if low in skip:
                    i += 1
                cand = []
        else:
            cand = [t]
        for c in cand:
            m = HOST.match(c)
            if m:
                hosts.append(m.group(1).lower())
            elif "://" in c:
                return f"看不出 {c} 访问哪里"
        i += 1
    allow = web_domains()
    if not hosts:
        return "上网的命令看不出访问哪里"
    for h in hosts:
        if h not in LOCAL and not any(h == d or h.endswith("." + d) for d in allow):
            return f"访问 {h}(不在 project.toml 的 [runner] web_domains 里)"
    return ""


def _tokens(segment: str) -> list[str]:
    tokens = [t.strip("'\"") for t in segment.split() if t.strip("'\"")]
    if tokens:
        tokens[0] = tokens[0].lstrip("({")
        if not tokens[0]:
            tokens = tokens[1:]
    while tokens and (tokens[0] in ("&", ".", "call", "command") or (tokens[0] == "env" and len(tokens) > 1)
                      or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0])):
        tokens = tokens[1:]
    return [t.rstrip(")}") for t in tokens]


def _secret(token: str) -> bool:
    name = re.split(r"[\\/]", token)[-1].lower()
    if name in (".env.example", "env.example"):
        return False
    return bool(name == ".env" or name.startswith(".env.") or re.search(r"\.(pem|key|p12|pfx)$", name)
                or name.startswith(("id_rsa", "id_ed25519")) or "credentials" in name)


def _exe(token: str) -> str:
    """命令的名字:去掉路径和 .exe,这样 C:\\Windows\\System32\\net.exe 也认得出来。"""
    return re.split(r"[\\/]", token)[-1].lower().removesuffix(".exe")


def _os_reason(tokens: list[str]) -> str:
    """系统能力。拦的理由不是"危险",是"一次就回不来":改密码、改权限、动磁盘都不能撤销。"""
    head = _exe(tokens[0])
    rest = [t.lower() for t in tokens[1:]]
    sub = rest[0] if rest else ""
    if (head == "net" and sub in ACCOUNT_SUB) or head in ACCOUNT_HEADS or head in ACCOUNT_PS:
        return "改账户或密码(net user / net localgroup / Set-LocalUser 这一类)"
    if (head == "reg" and sub in REG_WRITE) or head == "regedit":
        return "写注册表"
    if head in REG_PS and any(REG_PATH.search(t) for t in tokens[1:]):
        return "写注册表"
    if (head == "sc" and sub in SERVICE_SUB) or head in SERVICE_HEADS:
        return "装或改系统服务"
    if (head == "schtasks" and sub in TASK_SUB) or head in TASK_HEADS:
        return "建或改计划任务"
    if head == "set-executionpolicy" or any(t.startswith("-executionpolicy") for t in rest):
        return "改执行策略(会放开脚本)"
    if head == "takeown" or (head in ("icacls", "cacls") and any(t.startswith(ACL_FLAG) for t in rest)):
        return "改文件或目录的权限、所有者"
    if head in DISK_HEADS:
        return "动磁盘或启动项"
    if head in ("vssadmin", "wbadmin") and "delete" in rest:
        return "删卷影副本或备份"
    if (head == "netsh" and sub in ("advfirewall", "winsock", "winhttp", "firewall")) or head in FIREWALL_HEADS:
        return "改防火墙或防御设置"
    if head in VAULT_HEADS:
        return "动凭据库"
    if head in OPAQUE_HEADS:
        return "看不出会执行什么(rundll32 / wmic / mshta 这一类)"
    if head in ("runas", "sudo") or (head == "start-process" and "runas" in rest):
        return "提权执行"
    if head in ("ssh", "scp", "sftp") or any("git@github.com" in t or "ssh://" in t for t in tokens):
        return "用 SSH 出去:那是人的身份,不是 App 的身份(Agent 只经 bot.py 走 https)"
    if head in ("ssh-keygen", "ssh-add", "ssh-agent") or any("authorized_keys" in t for t in rest):
        return "动 SSH 密钥"
    return ""


def _git_reason(tokens: list[str], via_bot: bool) -> str:
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i] == "-c" and i + 1 < len(tokens) and tokens[i + 1].lower().startswith("core.hookspath"):
            return "git -c core.hooksPath(跳过 hook)"
        i += 2 if tokens[i] in GIT_OPTS_WITH_ARG else 1
    if i >= len(tokens):
        return ""
    sub, rest = tokens[i], tokens[i + 1:]
    opts = [t for t in rest if t.startswith("-")]
    opts += [f"-{ch}" for t in rest if re.fullmatch(r"-[A-Za-z]{2,}", t) for ch in t[1:]]
    args = [t for t in rest if not t.startswith("-")]
    if sub == "push":
        if PUSH_BAD & set(opts) or any(o.startswith("--force-with-lease") for o in opts):
            return "git push 的强推、删除或跳过 hook"
        if any(a.startswith("+") or a.startswith(":") for a in args):
            return "git push 的 +refspec(强推)/ :ref(删除)"
        if any(a == "main" or a.endswith(":main") or a.endswith("refs/heads/main") for a in args):
            return "直接推送 main(main 只通过合并 PR 变化)"
        if not via_bot:
            return "git push 要经 bash scripts/github/bot.sh <dev|pm> git push(Agent 用 App 的身份推送)"
    if sub == "rebase":
        return "git rebase(基线用 merge 合入)"
    if sub == "reset" and "--hard" in opts:
        return "git reset --hard"
    if sub == "clean":
        return "git clean"
    if sub == "checkout" and ("--" in rest or args == ["."]):
        return "git checkout -- <路径>(丢弃改动)"
    if sub == "restore" and "--staged" not in opts:
        return "git restore(丢弃改动)"
    if sub == "branch" and ("-D" in opts or (("-d" in opts or "--delete" in opts) and ("-f" in opts or "--force" in opts))):
        return "git branch 的强制删除"
    if sub == "tag" and ("-d" in opts or "--delete" in opts):
        return "git tag -d"
    if sub == "commit" and ("--no-verify" in opts or "-n" in opts):
        return "git commit --no-verify / -n"
    if sub == "config" and any(a.lower() == "core.hookspath" for a in args):
        return "git config core.hooksPath(跳过 hook)"
    return ""


def _gh_words(rest: list[str]) -> list[str]:
    words, skip = [], False
    for t in rest:
        if skip:
            skip = False
            continue
        if t in GH_OPTS_WITH_ARG:
            skip = True
            continue
        if not t.startswith("-"):
            words.append(t)
    return words


def _label_args(rest: list[str], which: tuple[str, ...] = ("--add-label", "--remove-label", "--label", "-l")) -> list[str]:
    out = []
    for k, t in enumerate(rest):
        if t in which and k + 1 < len(rest):
            out += rest[k + 1].split(",")
        elif t.startswith(tuple(w + "=" for w in which)):
            out += t.split("=", 1)[1].split(",")
    return [l.strip() for l in out]


def _api_method(rest: list[str]) -> str:
    if sum(t in ("-X", "--method") or bool(re.fullmatch(r"-X.+|--method=.+", t)) for t in rest) > 1:
        return "MULTIPLE"                      # gh uses the last one; never guess
    for k, t in enumerate(rest):
        if t in ("-X", "--method") and k + 1 < len(rest):
            return rest[k + 1].upper()
        m = re.fullmatch(r"(?:-X|--method=)([A-Za-z]+)", t)
        if m:
            return m.group(1).upper()
    if any(t in ("-f", "-F", "--field", "--raw-field", "--input") or t.startswith(("-f", "-F", "--field=", "--raw-field=", "--input="))
           for t in rest):
        return "POST"
    return "GET"


def _gh_reason(tokens: list[str], bot_role: str) -> str:
    rest = tokens[1:]
    words = _gh_words(rest)
    if not words:
        return ""
    pair = (words[0], words[1] if len(words) > 1 else "")
    if pair == ("pr", "merge"):
        if bot_role != "dev" or not {"--squash", "-s"} & set(rest) or {"--admin", "--auto", "--merge", "-m", "--rebase", "-r"} & set(rest):
            return "合并 PR(只许集成 Agent 经 bot.sh dev 用 --squash)"
        return ""
    if pair == ("workflow", "run") or pair[0] == "run" and pair[1] in ("rerun", "cancel"):
        return "触发或重跑工作流(发布只由人运行)"
    if pair[0] == "release" and pair[1] not in ("view", "list"):
        return "操作 Release(由发布工作流创建)"
    if pair[0] in ("auth", "extension", "alias", "config", "secret", "variable", "ruleset", "repo") and pair not in GH_READ:
        return f"gh {pair[0]}(Agent 不用)"
    labels = _label_args(rest) if pair[1] in ("create", "edit") else _label_args(rest, ("--add-label", "--remove-label"))
    if any(lab in HUMAN_LABELS for lab in labels) or (pair[0] == "label" and any(l in rest for l in HUMAN_LABELS)):
        return "加或去掉人专用标签(设计已批准、已验收、免验收)"
    if "需人定版" in _label_args(rest, ("--remove-label",)):
        return "去掉 需人定版(只由人去掉)"
    if pair == ("pr", "review") and bot_role != "review" and \
            any(re.fullmatch(r"(--approve|-a|--request-changes|-r)(=.*)?", t) for t in rest):
        return "批准或要求修改(只许经 bot.sh review 的评审 App;PM 只写 --comment)"
    if pair[0] == "api":
        method = _api_method(rest)
        if method == "GET":
            return ""
        path = pair[1]
        if bot_role == "dev" and re.search(r"(^|/)repos/[^/]+/[^/]+/milestones(/\d+)?$", path):
            return ""
        return "gh api 的写操作(只允许开发 App 经 bot.sh 写里程碑)"
    if pair in GH_READ:
        return ""
    if not bot_role:
        return "gh 的写操作要经 bash scripts/github/bot.sh(Agent 不用人的账号写 GitHub)"
    return ""


HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def strip_heredocs(command: str) -> str:
    """去掉 heredoc 的正文(写进评论的文字),留下命令行本身。"""
    out, end = [], None
    for line in command.split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        out.append(line)
        m = HEREDOC.search(line)
        if m:
            end = m.group(2)
    return "\n".join(out)


def reason(command: str, depth: int = 0) -> str:
    if depth == 0:
        command = strip_heredocs(command)
    if SECRET_VARS.search(command):
        return "引用了密钥的环境变量"
    for segment in SEGMENT.split(command):
        tokens = _tokens(segment)
        if not tokens:
            continue
        head = tokens[0].lower()
        if tokens == ["env"] or head in ("printenv", "set") and len(tokens) == 1 or \
                head in ("get-childitem", "gci", "dir", "ls") and any(t.lower().startswith("env:") for t in tokens[1:]):
            return "显示环境变量(可能包含密钥)"
        if head in SHELLS and depth < 3:
            for k, t in enumerate(tokens[1:], start=1):
                if (t.lower() in ("-command", "/c") or re.fullmatch(r"-[a-z]*c", t)) and k + 1 < len(tokens):
                    r = reason(" ".join(tokens[k + 1:]), depth + 1)
                    if r:
                        return r
                    break
        r = _os_reason(tokens)
        if r:
            return r
        bot_role = ""
        for k, t in enumerate(tokens[:2]):
            if t.replace("\\", "/").endswith(BOT) and len(tokens) > k + 2:
                bot_role, tokens = tokens[k + 1], tokens[k + 2:]
                head = tokens[0].lower()
                break
        if head == "git" or head.endswith(("/git", "\\git", "git.exe")):
            r = _git_reason(tokens, bot_role in ("dev", "pm"))
            if r:
                return r
        if head == "gh" or head.endswith(("/gh", "\\gh", "gh.exe")):
            r = _gh_reason(tokens, bot_role)
            if r:
                return r
        if head in NET:
            r = _net_reason(tokens)
            if r:
                return r
        if head in READERS and any(_secret(t) for t in tokens[1:]):
            return "读取密钥文件"
    return ""


def main() -> int:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        data = json.loads(sys.stdin.read() or "{}")
        command = (data.get("tool_input") or {}).get("command") or ""
        if not isinstance(command, str):
            raise ValueError("command is not a string")
        r = reason(command)
    except Exception as e:                       # a guard that cannot read its input must not let the command through
        print(f"guard_bash: 读不懂工具调用的输入,已拦下({type(e).__name__})", file=sys.stderr)
        return 2
    if r:
        print(f"guard_bash: 已拦下这条命令({r})。按 docs/运营规则.md 的规则,请人来做或换一种做法。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
