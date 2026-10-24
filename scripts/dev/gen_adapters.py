"""由 agents/*.md 和 commands/*.md 生成两种 harness 的文件(docs/运营规则.md 10 章)。只维护 agents/ 和 commands/ 这一份。

    python scripts/dev/gen_adapters.py            # 生成
    python scripts/dev/gen_adapters.py --check    # 只检查生成的文件是否和定义一致(不一致退出码 1;CI 也跑)

生成:
  Claude Code: .claude/agents/<名>.md(子 Agent;只读的只给 Read/Grep/Glob/Bash;模型 strong→opus、fast→sonnet,
               由环境变量映射到 DeepSeek 的模型)、.claude/commands/<名>.md(让主会话交给对应的子 Agent)
  OpenCode:    .opencode/agents/<名>.md(只读的 edit: deny;模型 <provider>/<project.toml 的 models>;
               steps = [runner] max_turns 里这个身份的值)、
               .opencode/commands/<名>.md(agent + subtask: true)
agents/ 的头部字段: name、description、tier(strong|fast)、readonly(true|false)、bot(dev|pm|review:写进正文开头的 GitHub 身份)、
bash_allow(可省略;只读的 Agent 在 OpenCode 里另外放行的命令,用 ; 分隔)。
只读的 Agent:Claude Code 只给 Read/Grep/Glob/Bash(Bash 不受限,靠约定和命令监视);OpenCode 里 edit 拒绝,bash 默认要确认,
只放行读取的 git 命令、date、bot.sh review、闸门和检验的脚本,以及 bash_allow。
commands/ 的头部字段: description、agent。正文原样使用($ARGUMENTS 两种 harness 都支持)。
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print("gen_adapters: 需要 Python 3.11 以上", file=sys.stderr)
    sys.exit(2)

import argparse  # noqa: E402
import json  # noqa: E402
import tomllib  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NOTE = "<!-- 由 scripts/dev/gen_adapters.py 从 {src} 生成。不要手改,改 {src} 后重新生成。 -->"
CLAUDE_MODEL = {"strong": "opus", "fast": "sonnet"}
IDENTITY = "你在 GitHub 上的身份:所有对 GitHub 的操作(包括读取、git fetch、git push)都用 `bash scripts/github/bot.sh {bot} ...`。"
READONLY_BASH = ["git fetch*", "git show*", "git log*", "git diff*", "git branch -r*", "git rev-parse*", "date*",
                 "bash scripts/github/bot.sh review*", "python scripts/github/gates.py*", "python scripts/ci/verify.py*"]


def parse(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"gen_adapters: {path} 没有头部(---)")
    head, body = text[4:].split("\n---\n", 1)
    meta = {}
    for line in head.splitlines():
        if line.strip():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body.lstrip("\n")


def q(text: str) -> str:
    """A YAML double-quoted scalar (JSON strings are valid YAML), so that "#", ":" and quotes in Chinese text stay text."""
    return json.dumps(text, ensure_ascii=False)


def build() -> dict[Path, str]:
    conf = tomllib.loads((ROOT / "project.toml").read_text(encoding="utf-8"))
    models, turns = conf.get("models", {}), conf.get("runner", {}).get("max_turns", {})
    provider = models.get("opencode_provider", "deepseek")
    out: dict[Path, str] = {}
    for f in sorted((ROOT / "agents").glob("*.md")):
        m, body = parse(f)
        name, tier, ro = m["name"], m["tier"], m["readonly"] == "true"
        if m.get("bot") not in ("dev", "pm", "review") or (ro and m["bot"] != "review"):
            raise SystemExit(f"gen_adapters: {f} 的 bot 要是 dev、pm 或 review(只读的 Agent 用 review)")
        body = IDENTITY.format(bot=m["bot"]) + "\n\n" + body
        if name != f.stem or tier not in CLAUDE_MODEL:
            raise SystemExit(f"gen_adapters: {f} 的 name 要等于文件名,tier 要是 strong 或 fast")
        note = NOTE.format(src=f"agents/{f.name}")
        claude = ["---", f"name: {name}", f"description: {q(m['description'])}"]
        if ro:
            claude.append("tools: Read, Grep, Glob, Bash")
        claude += [f"model: {CLAUDE_MODEL[tier]}", "---", note, "", body]
        out[Path(".claude/agents") / f.name] = "\n".join(claude)
        oc = ["---", f"description: {q(m['description'])}", "mode: all", f"model: {provider}/{models[tier]}"]
        if m["bot"] in turns:
            oc.append(f"steps: {int(turns[m['bot']])}")
        if ro:
            extra = [c.strip() for c in m.get("bash_allow", "").split(";") if c.strip()]
            oc += ["permission:", "  edit: deny", "  bash:", '    "*": ask'] + [f'    "{c}": allow' for c in READONLY_BASH + extra]
        oc += ["---", note, "", body]
        out[Path(".opencode/agents") / f.name] = "\n".join(oc)
    for f in sorted((ROOT / "commands").glob("*.md")):
        m, body = parse(f)
        note = NOTE.format(src=f"commands/{f.name}")
        out[Path(".claude/commands") / f.name] = "\n".join(
            ["---", f"description: {q(m['description'])}", "---", note, "",
             f"用 Agent 工具(旧名 Task)把下面的任务交给子 Agent `{m['agent']}`(subagent_type: {m['agent']}),把参数原样传过去,"
             "不要在当前会话里自己做。没有 Agent 工具时停止,告诉人。", "", body])
        out[Path(".opencode/commands") / f.name] = "\n".join(
            ["---", f"description: {q(m['description'])}", f"agent: {m['agent']}", "subtask: true", "---", note, "", body])
    return out


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="由 agents/ 和 commands/ 生成两种 harness 的文件")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    files = build()
    stale = [p for p, text in files.items()
             if not (ROOT / p).is_file() or (ROOT / p).read_text(encoding="utf-8") != text]
    if args.check:
        for p in stale:
            print(f"  不一致: {p}")
        print(f"gen_adapters --check: {len(files)} 个文件,不一致 {len(stale)}")
        return 1 if stale else 0
    for p in stale:
        (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / p).write_bytes(files[p].encode("utf-8"))
    print(f"gen_adapters: {len(files)} 个文件,更新 {len(stale)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
